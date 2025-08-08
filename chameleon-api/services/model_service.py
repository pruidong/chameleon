# /services/model_service.py
"""
模型服务模块，负责调用外部AI模型进行处理，如合规检查、翻译、图片编辑等。
"""

import base64
import json
import mimetypes
from http import HTTPStatus
from io import BytesIO

import requests
from PIL import Image
from dashscope import ImageSynthesis

from services.config import Config


def compliance_check(prompt: str):
    """
    调用硅基流动 Qwen3 模型进行合规性检查。
    :param prompt: 待检查的文本提示词
    :raises PermissionError: 如果内容不合规
    :raises Exception: 如果调用模型失败
    """
    if not prompt.strip():
        raise Exception("提示词不能为空")

    compliance_prompt = (
        f"不要推理，直接返回。请检查以下文本是否包含任何违法不良信息、敏感内容或成人内容。"
        f"如果包含，请仅返回大写的 'DISALLOWED'；如果不包含，请仅返回大写的 'ALLOWED'。"
        f"文本内容：{prompt}"
    )
    compliance_payload = {
        "model": "Qwen/Qwen3-8B",
        "messages": [
            {"role": "user", "content": compliance_prompt}
        ],
        "max_tokens": 10,  # 合规检查不需要长输出
        "stream": False
    }
    headers = {
        "Authorization": f"Bearer {Config.SILICON_FLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    compliance_response = requests.post(
        Config.SILICON_FLOW_LLM_URL,
        json=compliance_payload,
        headers=headers
    )
    if compliance_response.status_code == 200:
        compliance_data = compliance_response.json()
        # 安全访问响应内容
        try:
            compliance_text = compliance_data['choices'][0]['message']['content'].strip().upper()
        except (KeyError, IndexError):
            raise Exception(f"合规检查模型返回格式错误: {compliance_data}")

        if compliance_text == 'DISALLOWED':
            raise PermissionError("提示词包含不允许的内容")
    else:
        raise Exception(f"硅基流动合规检查失败: {compliance_response.text}")


def call_silicon_flow_qwen3(prompt: str):
    """
    调用硅基流动 Qwen3 模型进行翻译和合规检测。
    :param prompt: 原始中文提示词
    :return: 翻译后的英文提示词
    :raises ValueError: 如果翻译失败或响应格式错误
    :raises Exception: 如果调用模型失败
    """
    # 1. 合规检测 (已在 compliance_check 中实现)
    compliance_check(prompt)

    # 2. 翻译
    translate_prompt = (
        f"不要推理，直接返回。请将以下中文文本翻译成英文。"
        f"请严格按以下JSON格式输出，不要包含其他内容：{{\"en_prompt\": \"<英文翻译>\"}}"
        f"文本内容：{prompt}"
    )
    headers = {
        "Authorization": f"Bearer {Config.SILICON_FLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    translate_payload = {
        "model": "Qwen/Qwen3-8B",
        "messages": [
            {"role": "user", "content": translate_prompt}
        ],
        "max_tokens": 512,
        "stream": False
    }
    translate_response = requests.post(
        Config.SILICON_FLOW_LLM_URL,
        json=translate_payload,
        headers=headers
    )
    if translate_response.status_code == 200:
        translate_data = translate_response.json()
        try:
            content = translate_data['choices'][0]['message']['content']
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            en_prompt_json = json.loads(content)
            en_prompt = en_prompt_json.get('en_prompt', '')
            if not en_prompt:
                raise ValueError("翻译未能生成 'en_prompt'")
            return en_prompt
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise ValueError(f"解析翻译响应失败: {e}。响应内容: {content}")
    else:
        raise Exception(f"硅基流动翻译失败: {translate_response.text}")


def encode_file(file_path):
    """
    将图片文件编码为 Base64 Data URL。
    :param file_path: 图片文件路径
    :return: Base64 编码的 Data URL 字符串
    :raises ValueError: 如果文件不是支持的图像格式
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type or not mime_type.startswith("image/"):
        raise ValueError("不支持或无法识别的图像格式")
    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:{mime_type};base64,{encoded_string}"


def call_bailian(file_path: str, prompt_text: str):
    """
    调用百炼平台 API 进行图片编辑。
    :param file_path: 本地图片文件路径
    :param prompt_text: 编辑指令 (英文)
    :return: 处理后图片的 Base64 编码字符串
    :raises Exception: 如果调用失败或处理失败
    """
    # 再次进行合规检查 (虽然前端可能已检查，但后端也应确保)
    compliance_check(prompt_text)

    model_id = Config.BAILIAN_MODEL_ID
    api_key = Config.BAILIAN_API_KEY
    image_file_path = f'file://{file_path}'

    rsp = ImageSynthesis.call(
        api_key=api_key,
        model=model_id,
        function="description_edit",
        prompt=prompt_text,
        base_image_url=image_file_path,
        n=1
    )

    if rsp.status_code == HTTPStatus.OK:
        # 安全访问结果
        try:
            results = rsp.output.results
            if not results:
                raise Exception("ModelScope API returned no results")
            image_url = results[0].url # 假设只处理第一张图
        except (AttributeError, IndexError):
            raise Exception(f"ModelScope API returned unexpected data structure: {rsp}")

        # print(f"处理后的图片地址: {image_url}") # 调试用
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            processed_image = Image.open(BytesIO(image_response.content))
            # 将处理后的图像保存为字节流
            img_byte_arr = BytesIO()
            processed_image.save(img_byte_arr, format='PNG')  # 或 'JPEG'
            img_byte_arr.seek(0)
            # 编码为Base64
            encoded_string = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            return encoded_string
        else:
            raise Exception(f"从 URL 下载处理后的图片失败: {image_url}, 状态码: {image_response.status_code}")
    else:
        # 提供更详细的错误信息
        error_msg = (f"调用 ModelScope API 失败: "
                     f"状态码={rsp.status_code}, "
                     f"错误码={getattr(rsp, 'code', 'N/A')}, "
                     f"消息={getattr(rsp, 'message', 'N/A')}")
        raise Exception(error_msg)
