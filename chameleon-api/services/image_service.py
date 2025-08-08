# /services/image_service.py
"""
图片服务模块，负责处理图片上传、保存、清理等操作。
"""

import datetime
import os
import sqlite3
import uuid

from werkzeug.utils import secure_filename

from services.config import Config


def allowed_file(filename):
    """
    检查文件扩展名是否在允许列表中。
    """
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def save_temp_image(file):
    """
    保存上传的临时图片文件。
    :param file: Flask request.files 对象
    :return: (unique_filename, file_path, file_url_path) 元组
    :raises ValueError: 如果文件类型或大小无效
    """
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 使用UUID生成唯一文件名，避免冲突和路径猜测
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        file_url_path = f"/chameleon-api/uploads/{unique_filename}"
        return unique_filename, file_path, file_url_path
    else:
        raise ValueError("文件类型或大小无效")


def get_temp_image_path(filename):
    """
    根据文件名获取临时图片的完整路径。
    """
    return os.path.join(Config.UPLOAD_FOLDER, filename)


def cleanup_expired_files():
    """
    清理过期的临时文件和数据库记录 (超过1小时)。
    """
    # print("Running cleanup task...") # 调试用，生产环境可移除
    cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=1)
    conn = None
    try:
        conn = sqlite3.connect(Config.DATABASE)
        cursor = conn.cursor()
        # 查询过期记录
        cursor.execute(
            "SELECT id, path FROM image_uploads WHERE created_at < ?",
            (cutoff_time.isoformat(),)
        )
        expired_records = cursor.fetchall()
        deleted_count = 0
        for record in expired_records:
            file_id, file_path = record
            # 删除文件
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_count += 1
            # 删除数据库记录
            cursor.execute("DELETE FROM image_uploads WHERE id = ?", (file_id,))
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
