# /services/config.py
"""
应用配置模块，集中管理所有配置项。
"""
import os


class Config:
    """应用配置类"""
    # Flask 密钥，用于会话签名等
    SECRET_KEY = os.environ.get('CHAMELEON_APP_SECRET_KEY') or 'secret_key'

    # 数据库文件路径
    DATABASE = os.path.join(os.path.dirname(__file__), 'chameleon.db')

    # 上传文件夹路径
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

    # 最大上传文件大小 (6MB)
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024

    # 允许上传的文件扩展名
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    # SM2 加密密钥 (应从环境变量或安全存储中获取)
    SM2_PRIVATE_KEY = os.environ.get(
        'CHAMELEON_APP_SM2_PRIVATE_KEY') or 'sm2_private_key'
    SM2_PUBLIC_KEY = os.environ.get(
        'CHAMELEON_APP_SM2_PUBLIC_KEY') or 'sm2_public_key'

    # 硅基流动 API 配置 (用于 Qwen3)
    SILICON_FLOW_API_KEY = os.environ.get(
        'CHAMELEON_APP_SILICON_FLOW_API_KEY') or 'silicon_flow_api_key'
    SILICON_FLOW_LLM_URL = "https://api.siliconflow.cn/v1/chat/completions"

    # 百炼平台 API 配置
    BAILIAN_API_KEY = os.environ.get('CHAMELEON_APP_BAILIAN_API_KEY') or 'bailian_api_key'
    # 百炼平台使用的模型ID
    BAILIAN_MODEL_ID = "wanx2.1-imageedit"

    # --- GitHub OAuth2 配置 ---
    GITHUB_CLIENT_ID = os.environ.get('CHAMELEON_APP_GITHUB_CLIENT_ID') or 'github_client_id'
    GITHUB_CLIENT_SECRET = os.environ.get('CHAMELEON_APP_GITHUB_CLIENT_SECRET') or 'github_client_secret'
    GITHUB_REDIRECT_URI = os.environ.get('CHAMELEON_APP_GITHUB_REDIRECT_URI') or 'github_redirect_url'
    GITHUB_AUTHORIZATION_URL = 'https://github.com/login/oauth/authorize'
    GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
    GITHUB_USER_INFO_URL = 'https://api.github.com/user'

    # --- Flask-Limiter 配置 ---
    # 使用 Redis 作为存储后端，用于限流
    RATELIMIT_STORAGE_URL = os.environ.get('CHAMELEON_APP_REDIS_URL') or "xxxxxx"  # 根据你的 Redis 配置修改
