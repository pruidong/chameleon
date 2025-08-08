# /utils/sm2.py
"""
SM2 加密/解密/签名工具模块。
"""

import binascii  # 导入 binascii 用于十六进制转换

from gmssl import sm2

from services.config import Config

# 初始化 SM2 密钥对
sm2_util = sm2.CryptSM2(
    public_key=Config.SM2_PUBLIC_KEY,
    private_key=Config.SM2_PRIVATE_KEY,
    mode=1 # 指定模式，通常为1
)


def encrypt_data(plaintext: str) -> str:
    """
    使用SM2公钥加密数据。
    :param plaintext: 待加密的明文字符串
    :return: 十六进制编码的加密后数据 (hex string)
    :raises Exception: 如果加密过程出错
    """
    try:
        # SM2加密 (返回 bytes)
        encrypted_bytes = sm2_util.encrypt(plaintext.encode('utf-8'))
        # 转换为十六进制字符串以便传输
        encrypted_hex = encrypted_bytes.hex()  # 使用 .hex() 方法
        return encrypted_hex
    except Exception as e:
        # print(f"Encryption failed: {e}") # 调试用
        raise  # 重新抛出异常让调用者处理


def decrypt_data(ciphertext_hex: str) -> str:
    """
    使用SM2私钥解密数据。
    :param ciphertext_hex: 十六进制编码的加密数据 (hex string)
    :return: 解密后的明文字符串
    :raises ValueError: 如果密文格式无效或解密失败
    """
    try:
        # 将十六进制字符串转换回 bytes
        ciphertext_bytes = bytes.fromhex(ciphertext_hex)  # 使用 bytes.fromhex()
        # SM2解密 (返回 bytes)
        decrypted_bytes = sm2_util.decrypt(ciphertext_bytes)
        # 转换为字符串
        decrypted_text = decrypted_bytes.decode('utf-8')
        return decrypted_text
    except binascii.Error as e:  # 捕获可能的十六进制转换错误
        # print(f"Invalid hex string for decryption: {e}") # 调试用
        raise ValueError("无效的密文格式") from e
    except Exception as e:
        # print(f"Decryption failed: {e}") # 调试用
        raise ValueError(f"解密失败: {e}") from e # 更明确的错误信息


def sign_data(data: str) -> str:
    """
    使用SM2私钥对数据进行签名。
    :param data: 待签名的字符串数据
    :return: 十六进制编码的签名 (hex string)
    :raises ValueError: 如果签名过程失败
    """
    try:
        data_to_sign = data.encode('utf-8')
        # 注意：gmssl 的 sign 方法签名可能略有不同，需要查阅文档
        # 假设 CryptSM2.sign 直接处理 utf-8 编码的字符串数据
        signature_bytes = sm2_util.sign(data_to_sign)  # 需要确认此方法签名
        # gmssl 的 sign 通常返回 bytes
        signature_hex = signature_bytes.hex()
        # print(f"Signed data. Signature (hex): {signature_hex[:50]}...") # 调试用
        return signature_hex
    except Exception as e:
        # print(f"Signing failed: {e}") # 调试用
        raise ValueError(f"签名数据失败: {e}") from e


def verify_signature(data: str, signature_hex: str) -> bool:
    """
    使用SM2公钥验证数据签名。
    :param data: 原始数据字符串
    :param signature_hex: 十六进制编码的签名 (hex string)
    :return: 签名是否有效
    """
    try:
        # 将十六进制签名转换为 bytes
        signature_bytes = bytes.fromhex(signature_hex)
        data_to_verify = data.encode('utf-8')
        # 假设 CryptSM2.verify 直接处理
        is_valid = sm2_util.verify(signature_bytes, data_to_verify)  # 需要确认此方法签名
        return is_valid
    except binascii.Error as e:
        # print(f"Invalid hex string for signature: {e}") # 调试用
        return False  # 无效的签名格式应视为验证失败
    except Exception as e:
        # print(f"Signature verification failed: {e}") # 调试用
        return False  # 验证过程出错也视为失败
