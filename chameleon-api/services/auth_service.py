# /services/auth_service.py
"""
认证服务模块，负责处理用户认证逻辑，包括 GitHub OAuth2 流程。
"""

import datetime
import hashlib
import secrets
import sqlite3

import jwt
import requests

from services.config import Config


def get_db_connection():
    """
    获取数据库连接，并设置行工厂以便通过列名访问数据。
    """
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def hash_identifier(identifier: str) -> str:
    """
    对用户标识符（如 GitHub ID）进行 SHA256 哈希处理，用于安全存储。
    """
    return hashlib.sha256(identifier.encode()).hexdigest()


def get_github_authorize_url():
    """
    生成跳转到 GitHub 授权页面的 URL。
    前端需要重定向用户到此 URL。
    """
    import urllib.parse
    # GitHub 推荐的 scopes，根据需要调整
    scopes = "read:user"
    params = {
        "client_id": Config.GITHUB_CLIENT_ID,
        "redirect_uri": Config.GITHUB_REDIRECT_URI,
        "scope": scopes,
        "state": secrets.token_urlsafe(32)  # 防止CSRF攻击
    }
    # 将 state 临时存储起来，以便在回调时验证 (例如，存入 Redis 或 session)
    # 这里简化处理，实际应用中需要存储 state
    query_string = urllib.parse.urlencode(params)
    authorize_url = f"{Config.GITHUB_AUTHORIZATION_URL}?{query_string}"
    return authorize_url


def exchange_code_for_token(code: str):
    """
    使用授权码从 GitHub 获取访问令牌。
    """
    payload = {
        "code": code,
        "client_id": Config.GITHUB_CLIENT_ID,
        "client_secret": Config.GITHUB_CLIENT_SECRET,
        "redirect_uri": Config.GITHUB_REDIRECT_URI,
    }
    headers = {
        "Accept": "application/json"
    }
    response = requests.post(Config.GITHUB_TOKEN_URL, data=payload, headers=headers)
    response.raise_for_status()  # 如果状态码不是 2xx，会抛出异常
    token_data = response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise Exception(f"从 GitHub 获取访问令牌失败: {token_data}")
    return access_token


def get_github_user_info(access_token: str):
    """
    使用访问令牌获取 GitHub 用户信息。
    """
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/json"
    }
    response = requests.get(Config.GITHUB_USER_INFO_URL, headers=headers)
    response.raise_for_status()
    user_info = response.json()
    return user_info


def verify_github_login(code: str):
    """
    完成 GitHub OAuth2 登录流程。
    1. 用授权码换取访问令牌。
    2. 用访问令牌获取用户信息 (包括登录名和ID)。
    3. 生成 JWT 会话令牌。
    """
    try:
        # 1. 获取 Access Token
        access_token = exchange_code_for_token(code)
        # 2. 获取用户信息
        user_info = get_github_user_info(access_token)
        github_id = user_info.get('id')
        github_login = user_info.get('login')  # 获取 GitHub 用户名
        if not github_id:
            raise Exception("获取 GitHub 用户 ID 失败")
        # 使用 GitHub ID 作为唯一标识符
        identifier = str(github_id)
        # 3. (可选) 记录用户登录 (如果需要限制登录次数，可以基于 github_id)
        # 此处简化，不实现登录次数限制
        # 4. 生成JWT会话令牌
        hashed_identifier = hash_identifier(identifier)  # 复用哈希函数
        payload = {
            'identifier': hashed_identifier,  # 存储哈希后的标识符
            'github_login': github_login,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)  # 7天过期
        }
        token = jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')
        # 返回 token 和 github_login
        return token, github_login  # <-- 修改：返回用户名
    except requests.exceptions.RequestException as e:
        raise Exception(f"GitHub OAuth 过程中网络错误: {e}")
    except Exception as e:
        raise Exception(f"GitHub 登录失败: {e}")
