# -*- encoding: utf-8 -*-
import os
from dotenv import load_dotenv

class BaseConfig():
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
    load_dotenv(os.path.join(BASE_DIR, ".env"))

    azure_speech_key = os.getenv('azure_speech_key')
    azure_speech_region = os.getenv('azure_speech_region')

    azure_translator_key = os.getenv('azure_translator_key')
    azure_translator_location = os.getenv('azure_translator_location')

    azure_computer_vision_key = os.getenv('azure_computer_vision_key')
    azure_computer_vision_endpoint = os.getenv('azure_computer_vision_endpoint')

    afd_host_name = os.getenv('afd_host_name')
    afd_host_ip = os.getenv('afd_host_ip')

    admin_password = os.getenv('admin_password')

    db_path = os.path.join(BASE_DIR, "db.sqlite")

    debug = False

    def open_debug():
        BaseConfig.debug = True