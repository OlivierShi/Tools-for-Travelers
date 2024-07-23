# -*- encoding: utf-8 -*-
import os
from dotenv import load_dotenv

class BaseConfig():
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
    load_dotenv(os.path.join(BASE_DIR, ".env"))

    azure_speech_key = os.getenv('azure_speech_key')
    azure_speech_region = os.getenv('azure_speech_region')