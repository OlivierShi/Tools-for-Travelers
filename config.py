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

    afd_host_name = os.getenv('afd_host_name')
    afd_host_ip = os.getenv('afd_host_ip')

    db_path = os.path.join(BASE_DIR, "db.sqlite")
