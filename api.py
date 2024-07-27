from flask import Flask, request, jsonify, send_file, render_template, url_for
from flask_cors import CORS
import requests
import uuid
import json
import os
from pydub import AudioSegment
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from urllib.parse import urlparse
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from config import BaseConfig
from translation_manager import TranslationManager
from sqlite import SQLiteStorage
from datetime import datetime
import time
import argparse


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

def do_ocr(input_image_url, output_image_filepath):
    client = ImageAnalysisClient(
        endpoint=BaseConfig.azure_computer_vision_endpoint,
        credential=AzureKeyCredential(BaseConfig.azure_computer_vision_key)
    )

    if BaseConfig.debug:
        mock_image ="https://learn.microsoft.com/azure/ai-services/computer-vision/media/quickstarts/presentation.png"
        result = client.analyze_from_url(image_url=mock_image, visual_features=[VisualFeatures.READ])


        # Fetch the image
        response = requests.get(mock_image)
        response.raise_for_status()  # Ensure the request was successful
        # Convert the response content to a numpy array
        image_array = np.frombuffer(response.content, np.uint8)

        # Decode the numpy array as an image
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    else:
        result = client.analyze_from_url(image_url=input_image_url, visual_features=[VisualFeatures.READ])
        filename = input_image_url.split("/")[-1]
        file_path = os.path.join(BaseConfig.BASE_DIR, f"static/camera/images/{filename}")
        img = cv2.imread(file_path)

    pil_img = Image.fromarray(img)
    draw = ImageDraw.Draw(pil_img)
    font_path = os.path.join(BaseConfig.BASE_DIR, "static/NotoSansCJK-Regular.ttc")
    font = ImageFont.truetype(font_path, size=20)

    if result.read is not None and len(result.read.blocks[0].lines)> 0:
        lines = result.read.blocks[0].lines
        for line in lines:
            words = line['words']
            for word in words:
                tl = (word['boundingPolygon'][0]["x"], word['boundingPolygon'][0]["y"])
                tr = (word['boundingPolygon'][1]["x"], word['boundingPolygon'][1]["y"])
                br = (word['boundingPolygon'][2]["x"], word['boundingPolygon'][2]["y"])
                bl = (word['boundingPolygon'][3]["x"], word['boundingPolygon'][3]["y"])

                text = word['text']

                print(text)
                
                # Draw bounding box
                pts = np.array([tl, tr, br, bl], np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(img, [pts], isClosed=True, color=(0, 0, 255), thickness=2)
                
                # Put text
                draw.text((tl[0], tl[1] - 40), text, font=font, fill=(255, 255, 255))
    img_with_text = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    cv2.imwrite(output_image_filepath, img_with_text)

def process_wav(wav_bytes, channels=1, frame_rate=16000):
    # Convert bytes data to AudioSegment
    audio = AudioSegment.from_file(BytesIO(wav_bytes), format="webm")
    
    audio = audio.set_channels(channels)
    audio = audio.set_frame_rate(frame_rate)
    
    output_io = BytesIO()
    audio.export(output_io, format="wav", codec="pcm_s16le")
    return output_io.getvalue()

@app.route('/translator/api/sr', methods=['POST'])
def speech_recognition():
    uuid = request.headers.get('Recording-UUID')
    lang = request.headers.get("lang")  # the language of the speech to be recognized
    password = request.headers.get("password")
    print(f"Password: {password}")
    print(BaseConfig.admin_password)
    if password != BaseConfig.admin_password:
        return jsonify({'error': 'Unauthorized'}), 401
    
    print(f"Request received for speech recognition\n{uuid}")

    audio_data = request.data

    processed_audio_data = process_wav(audio_data)
    recognized_text = recognize_from_audio_api(processed_audio_data, lang)

    datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tm.save_translation(id=uuid, datetime=datetime_str, Chinese=recognized_text)

    print(f"Recognized text: {recognized_text}")
    return jsonify({"message": recognized_text}), 200


@app.route('/translator/api/translate', methods=['POST'])
def translate():
    uuid = request.headers.get('Recording-UUID')
    lang = request.headers.get("lang")  # the language of the text to be translated
    password = request.headers.get("password")

    if password != BaseConfig.admin_password:
        return jsonify({'error': 'Unauthorized'}), 401
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

@app.route('/translator/api/tts', methods=['POST'])
def text_to_speech():
    uuid = request.headers.get('Recording-UUID')
    lang = request.headers.get("lang")  # the language of the text to be spoken
    password = request.headers.get("password")

    if password != BaseConfig.admin_password:
        return jsonify({'error': 'Unauthorized'}), 401    
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

@app.route('/translator/api/history', methods=['GET'])
def get_history():
    password = request.headers.get("password")

    if password != BaseConfig.admin_password:
        return jsonify({'error': 'Unauthorized'}), 401
        
    history = tm.get_translation_history()
    sorted_history = sorted(history, key=lambda x: x["datetime"], reverse=True)

    return jsonify(sorted_history), 200


@app.route('/translator.html')
def translator():
    print(request.base_url)
    endpoint = str(request.base_url)
    if not ("localhost" in endpoint or "127.0.0.1" in endpoint or endpoint.startswith("https")):
        endpoint = endpoint.replace("http", "https")

    endpoint = endpoint.replace(BaseConfig.afd_host_ip, BaseConfig.afd_host_name).replace("/translator.html", "")
        
    return render_template('translator.html', endpoint=endpoint)


# Camera

if not os.path.exists('static/camera/images'):
    os.makedirs('static/camera/images')

@app.route('/camera/api/ocr', methods=['POST'])
def ocr():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    endpoint = str(request.host_url)
    if not ("localhost" in endpoint or "127.0.0.1" in endpoint or endpoint.startswith("https")):
        endpoint = endpoint.replace("http", "https")

    endpoint = endpoint.replace(BaseConfig.afd_host_ip, BaseConfig.afd_host_name).replace("/camera.html", "")

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # Generate a unique filename using UUID
        file_id = uuid.uuid4()
        filename = f"ori_{file_id}.png"
        output_filename = f"ocr_{file_id}.png"
        filepath = os.path.join('static/camera/images', filename)
        output_filepath = os.path.join('static/camera/images', output_filename)
        
        # Save the file to the images directory
        file.save(filepath)
        original_image_url = endpoint + f'static/camera/images/{filename}'
        do_ocr(original_image_url, output_filepath)
        
        # Create the URL to the saved image
        image_url = endpoint + f'static/camera/images/{output_filename}'
        
        # Return the URL as JSON response
        return jsonify({'newImageUrl': image_url}), 200

@app.route('/camera.html')
def camera():
    print(request.host_url)
    endpoint = str(request.host_url)
    if not ("localhost" in endpoint or "127.0.0.1" in endpoint or endpoint.startswith("https")):
        endpoint = endpoint.replace("http", "https")

    endpoint = endpoint.replace(BaseConfig.afd_host_ip, BaseConfig.afd_host_name).replace("/camera.html", "")
        
    return render_template('camera.html', endpoint=endpoint)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A simple argparse example")
    
    parser.add_argument('--debug', action='store_true', help="Debug mode")

    args = parser.parse_args()

    ip = "0.0.0.0"
    if args.debug:
        BaseConfig.open_debug()
        ip = "localhost"

    app.run(ip, port=8000) 