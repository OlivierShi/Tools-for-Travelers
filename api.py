from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import requests
import uuid
import json
from pydub import AudioSegment
from io import BytesIO
from config import BaseConfig
from translation_manager import TranslationManager
from sqlite import SQLiteStorage
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
SPEECH_KEY = BaseConfig.azure_speech_key
SERVICE_REGION = BaseConfig.azure_speech_region

TRANSLATOR_KEY = BaseConfig.azure_translator_key
TRANSLATOR_LOCATION = BaseConfig.azure_translator_location

db = SQLiteStorage(BaseConfig.db_path)

tm = TranslationManager(db)


def recognize_from_audio_api(audio_data, lang):
    if lang not in ["zh", "ru"]:
        raise ValueError("Language not supported")
    
    language = "zh-CN" if lang == "zh" else "ru-RU"
    url = f"https://{SERVICE_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
    params = {
        "language": language,
        "format": "detailed"
    }

    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
        "Content-Type": "audio/wav"
    }

    response = requests.post(url, headers=headers, params=params, data=audio_data)

    if response.status_code == 200:
        print("Transcription: ", response.json())
        return response.json()["DisplayText"]
    else:
        print(f"Error: {response.status_code}")
        print(response.json())

    return None

def text_to_speech_api(text, lang):
    if lang not in ["zh", "ru"]:
        raise ValueError("Language not supported")
    
    if lang == "zh":
        language = "zh-CN"
        voice = "zh-CN-YunxiNeural"
    else:
        language = "ru-RU"
        voice = "ru-RU-DmitryNeural"

    url = f"https://{SERVICE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    ssml_pattern = f"<speak xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xmlns:emo='http://www.w3.org/2009/10/emotionml' version='1.0' xml:lang='{language}'><voice name='{voice}' leadingsilence-exact='0ms' style='general' volume='190%%' rate='+10%%'>{text}</voice></speak>"

    headers = {
        "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
        "Content-Type": "application/ssml+xml",
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
    }

    response = requests.post(url, headers=headers, data=ssml_pattern.encode("utf-8"))
    if response.status_code != 200:
        print(response.text)
        return None
    
    return response.content
    
def translate_text(text, lang):
    if lang not in ["zh", "ru"]:
        raise ValueError("Language not supported")
    
    if lang == "zh":
        from_lang = "zh-Hans"
        to_lang = "ru"
    else:
        from_lang = "ru"
        to_lang = "zh-Hans"

    url = "https://api.cognitive.microsofttranslator.com/translate"

    params = {
        "api-version": "3.0",
        "from": from_lang,
        "to": [to_lang, 'en']
    }

    headers = {
        "Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
        'Ocp-Apim-Subscription-Region': TRANSLATOR_LOCATION,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{
        "text": text
    }]

    request = requests.post(url, params=params, headers=headers, json=body)
    response = request.json()
    return response[0]["translations"]


def process_wav(wav_bytes, channels=1, frame_rate=16000):
    # Convert bytes data to AudioSegment
    audio = AudioSegment.from_file(BytesIO(wav_bytes), format="webm")
    
    audio = audio.set_channels(channels)
    audio = audio.set_frame_rate(frame_rate)
    
    output_io = BytesIO()
    audio.export(output_io, format="wav", codec="pcm_s16le")
    return output_io.getvalue()

@app.route('/api/sr', methods=['POST'])
def speech_recognition():
    uuid = request.headers.get('Recording-UUID')
    lang = request.headers.get("lang")  # the language of the speech to be recognized
    print(f"Request received for speech recognition\n{uuid}")

    audio_data = request.data

    processed_audio_data = process_wav(audio_data)
    recognized_text = recognize_from_audio_api(processed_audio_data, lang)

    datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tm.save_translation(id=uuid, datetime=datetime_str, Chinese=recognized_text)

    print(f"Recognized text: {recognized_text}")
    return jsonify({"message": recognized_text}), 200


@app.route('/api/translate', methods=['POST'])
def translate():
    uuid = request.headers.get('Recording-UUID')
    lang = request.headers.get("lang")  # the language of the text to be translated
    text_to_translate = request.json["text"]

    print(f"Request received for translation\n{uuid}, {text_to_translate}")

    results = translate_text(text_to_translate, lang)
    ## [{"text": "Привет, мир!", "to": "ru"}, {"text": "Hello, world!", "to": "en"}]

    datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ru_text, en_text, zh_text = "", "", ""

    if lang == "zh":
        zh_text = text_to_translate
    else:
        ru_text = text_to_translate

    for item in results:
        if item["to"] == "ru":
            ru_text = item["text"]
        elif item["to"] == "en":
            en_text = item["text"]
        else:
            zh_text = item["text"]

    tm.save_translation(id=uuid, datetime=datetime_str, Chinese=zh_text, Russian=ru_text, English=en_text)

    print(f"Translated text: {results}")
    return jsonify({"translations": results}), 200

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    uuid = request.headers.get('Recording-UUID')
    lang = request.headers.get("lang")  # the language of the text to be spoken
    text = request.json["text"]

    print(f"Request received for TTS\n{uuid}, {text}")
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    tts = text_to_speech_api(text, lang)

    audio = AudioSegment(
        data=tts,
        sample_width=2,
        frame_rate=16000,
        channels=1
    )

    mp3_fp = BytesIO()
    audio.export(mp3_fp, format="mp3")
    mp3_fp.seek(0)
    return send_file(mp3_fp, mimetype='audio/mpeg', as_attachment=True, download_name='tts_output.mp3')

@app.route('/api/history', methods=['GET'])
def get_history():
    history = tm.get_translation_history()
    sorted_history = sorted(history, key=lambda x: x["datetime"], reverse=True)

    return jsonify(sorted_history), 200


@app.route('/home.html')
def home():
    print(request.base_url)
    endpoint = str(request.base_url)
    if not ("localhost" in endpoint or "127.0.0.1" in endpoint or endpoint.startswith("https")):
        endpoint = endpoint.replace("http", "https")

    if "/home.html" in endpoint:
        endpoint = endpoint.replace("/home.html", "")
        
    return render_template('home.html', endpoint=endpoint)

if __name__ == '__main__':
    app.run()