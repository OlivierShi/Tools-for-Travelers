# -*- encoding: utf-8 -*-
import os
from dotenv import load_dotenv
from PIL import ImageFont

class BaseConfig():
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
    load_dotenv(os.path.join(BASE_DIR, ".env"))

    azure_speech_key = os.getenv('azure_speech_key')
    azure_speech_region = os.getenv('azure_speech_region')

    azure_translator_key = os.getenv('azure_translator_key')
    azure_translator_location = os.getenv('azure_translator_location')

    azure_computer_vision_key = os.getenv('azure_computer_vision_key')
    azure_computer_vision_endpoint = os.getenv('azure_computer_vision_endpoint')

    openai_api_key = os.getenv('openai_api_key')
    openai_azure_endpoint = os.getenv('openai_azure_endpoint')
    openai_api_version = os.getenv('openai_api_version')
    openai_api_model = os.getenv('openai_api_model')   

    afd_host_name = os.getenv('afd_host_name')
    afd_host_ip = os.getenv('afd_host_ip')

    admin_password = os.getenv('admin_password')

    db_path = os.path.join(BASE_DIR, "db.sqlite")
    font_path = os.path.join(BASE_DIR, "static/NotoSansCJK-Regular.ttc")
    image_font_zh = ImageFont.truetype(font_path, size=20)
    
    debug = False

    def open_debug():
        BaseConfig.debug = True