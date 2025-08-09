# /app.py
"""
Flask 应用主入口，定义 API 路由和应用初始化逻辑。
"""

import os
import sqlite3

import jwt
from flask import Flask, request, jsonify, send_from_directory
from flask_apscheduler import APScheduler
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from services import auth_service, image_service, model_service
from services.config import Config
from utils.sm2 import decrypt_data  # 导入加密函数

app = Flask(__name__)
app.config.from_object(Config)

# 启用 CORS
CORS(app)

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# 初始化数据库
def init_db():
    """初始化数据库，创建所需表"""
    with app.app_context():
        db = sqlite3.connect(app.config['DATABASE'])
        cursor = db.cursor()
        with app.open_resource('services/schema.sql', mode='r') as f:
             db.cursor().executescript(f.read())
        db.commit()
        db.close()


# 初始化 Flask-Limiter 用于速率限制
limiter = Limiter(
    key_func=get_remote_address, # 使用客户端IP作为限流键
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://') # 默认使用内存存储
)


# 初始化 Flask-APScheduler 用于定时任务
scheduler = APScheduler()
scheduler.init_app(app)


@scheduler.task('interval', id='do_cleanup', hours=1)
def cleanup_task():
    """定时任务：每小时清理过期文件和数据库记录"""
    image_service.cleanup_expired_files()


# --- 辅助函数 ---

def get_session_data():
    """
    从请求头的 Authorization Bearer Token 中获取并验证 JWT 会话数据。
    :return: JWT 载荷 (payload) 字典
    :raises PermissionError: 如果令牌缺失、格式错误或已过期/无效
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise PermissionError("缺少或无效的 Authorization 头")
    token = auth_header.split(' ')[1]
    try:
        # 解码 JWT 令牌
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload  # 返回包含 identifier 和 github_login 的载荷
    except jwt.ExpiredSignatureError:
        raise PermissionError("会话已过期")
    except jwt.InvalidTokenError:
        raise PermissionError("无效的会话令牌")


# --- API 路由 ---

@app.route('/')
def index():
    """根路径，返回服务运行状态"""
    return "图像处理后端服务正在运行。"


# 1. 获取 GitHub 授权 URL
@app.route('/api/auth/github', methods=['GET'])
@limiter.limit("10 per minute") # 速率限制：每分钟最多10次
def github_auth():
    """
    前端调用此接口获取跳转到 GitHub 的授权 URL。
    """
    try:
        auth_url = auth_service.get_github_authorize_url()
        return jsonify({'auth_url': auth_url}), 200
    except Exception as e:
        app.logger.error(f"获取 GitHub 授权 URL 时出错: {e}")
        return jsonify({'error': '获取 GitHub 授权 URL 失败'}), 500


# 2. GitHub OAuth2 回调处理
@app.route('/api/auth/github/callback', methods=['POST'])
def github_callback():
    """
    处理前端发送的 GitHub 授权码，完成登录流程。
    """
    try:
        # 从请求体获取 JSON 数据
        data = request.get_json()
        if not data:
            return jsonify({'error': '缺少 JSON 数据'}), 400
        code = data.get('code')
        # state = data.get('state') # 可选：验证 state 以防止CSRF
        if not code:
            return jsonify({'error': '缺少授权码'}), 400

        # --- 调用认证服务完成登录 ---
        # 完成登录流程，获取 JWT 令牌 和 GitHub 用户名
        jwt_token, github_login = auth_service.verify_github_login(code)
        # --- 调用结束 ---

        return jsonify({
            'token': jwt_token,
            'identifier': github_login,  # 返回 GitHub 用户名作为标识符
            'message': '登录成功'
        }), 200

    except Exception as e:
        app.logger.error(f"处理 GitHub 回调时出错: {e}")
        # 提供更具体的错误信息给前端调试 (生产环境可酌情简化)
        return jsonify({'error': str(e)}), 400  # 或 500


# 3. 提示词翻译
@app.route('/api/translate', methods=['POST'])
@limiter.limit("20 per minute") # 速率限制：每分钟最多20次
def translate_prompt():
    """
    接收加密的中文提示词，进行解密、合规检查、翻译，返回加密的英文提示词。
    """
    try:
        # 从请求体获取 JSON 数据
        data = request.get_json()
        encrypted_prompt = data.get('prompt')
        if not encrypted_prompt:
            return jsonify({'error': '缺少提示词'}), 400

        # SM2 解密提示词
        prompt = decrypt_data(encrypted_prompt)

        # 调用模型服务进行翻译 (内部包含合规检查)
        en_prompt = model_service.call_silicon_flow_qwen3(prompt)

        # (可选) SM2 加密响应
        # encrypted_en_prompt = encrypt_data(en_prompt)
        # return jsonify({'en_prompt': encrypted_en_prompt}), 200

        return jsonify({'en_prompt': en_prompt}), 200

    except PermissionError as e:
        return jsonify({'error': str(e)}), 403  # 会话过期/无效 或 内容不合规
    except ValueError as e:  # 合规检查失败或翻译失败
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"翻译提示词时出错: {e}")
        return jsonify({'error': '翻译失败'}), 500


# 4. 静态文件服务 (用于访问上传的图片)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    提供对上传图片文件的访问。
    可以添加额外的权限检查，例如验证会话或文件归属。
    """

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# 5. 图片处理
@app.route('/api/process', methods=['POST'])
@limiter.limit("10 per minute") # 速率限制：每分钟最多10次
def process_image():
    """
    接收图片和加密提示词，进行解密、图片处理，返回处理后图片的 Base64 编码。
    """
    try:
        # 验证会话并获取用户信息
        session_data = get_session_data()  # 获取完整session数据
        hashed_identifier = session_data.get('identifier')
        github_login = session_data.get('github_login', 'unknown_user')

        # 获取上传的图片文件
        if 'image' not in request.files:
            return jsonify({'error': '未提供图片文件'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '未选择图片'}), 400

        # 获取其他表单参数
        # 注意：文件和非文件数据可能在不同部分 (request.files vs request.form)
        encrypted_prompt = request.form.get('prompt') # 从 form-data 获取
        if not encrypted_prompt:
            # 如果 form 中没有，尝试从 JSON body 获取 (不太常见于文件上传)
            json_data = request.get_json()
            encrypted_prompt = json_data.get('prompt') if json_data else None

        if not encrypted_prompt:
            return jsonify({'error': '缺少提示词'}), 400

        # SM2 解密提示词
        prompt = decrypt_data(encrypted_prompt)

        # 保存临时文件
        filename, file_path, file_url_path = image_service.save_temp_image(file)
        # image_url = f"{request.host_url.rstrip('/')}{file_url_path}" # 本地文件路径，非必需

        # 调用模型服务处理图片 (内部包含合规检查)
        result_b64 = model_service.call_bailian(file_path, prompt)

        # 保存上传记录到数据库 (使用 GitHub ID)
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        # 可以选择存储 github_login 以便查询
        cursor.execute(
            "INSERT INTO image_uploads (phone, filename, path) VALUES (?, ?, ?)",
            (hashed_identifier, f"{github_login}_{filename}", file_path)  # 示例：在文件名前加用户名
        )
        conn.commit()
        conn.close()

        return jsonify({'result': result_b64}), 200

    except PermissionError as e:
        return jsonify({'error': str(e)}), 403  # 会话过期/无效 或 内容不合规
    except ValueError as e:  # 文件类型/大小错误, 模型调用错误
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"处理图片时出错: {e}")
        return jsonify({'error': '图片处理失败'}), 500


if __name__ == '__main__':
    init_db()  # 初始化数据库
    scheduler.start()  # 启动定时任务
    # 注意：生产环境不要使用 debug=True
    app.run(debug=False, host='0.0.0.0', port=5001)

