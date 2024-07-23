from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import azure.cognitiveservices.speech as speechsdk
import base64
import os
from pydub import AudioSegment
from io import BytesIO
from config import BaseConfig

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
SPEECH_KEY = BaseConfig.azure_speech_key
SERVICE_REGION = BaseConfig.azure_speech_region

def recognize_from_audio_api(audio_data):

    url = f"https://{SERVICE_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
    params = {
        "language": "zh-CN",
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

def text_to_speech_api(text):
    url = f"https://{SERVICE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    zh_ssml_pattern = "<speak xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xmlns:emo='http://www.w3.org/2009/10/emotionml' version='1.0' xml:lang='zh-CN'><voice name='zh-CN-XiaoshuangNeural' leadingsilence-exact='0ms' style='general' volume='190%%' rate='+10%%'>%s</voice></speak>"

    body = zh_ssml_pattern % text
    headers = {
        "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
        "Content-Type": "application/ssml+xml",
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
    }

    response = requests.post(url, headers=headers, data=body.encode("utf-8"))
    if response.status_code != 200:
        print(response.text)
        return None
    
    return response.content
    
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
    print("Request received")
    audio_data = request.data

    processed_audio_data = process_wav(audio_data)
    recognized_text = recognize_from_audio_api(processed_audio_data)

    print(recognized_text)
    return jsonify({"message": recognized_text}), 200


@app.route('/api/translate', methods=['POST'])
def translate():
    print("Request received")
    text_to_translate = request.json["text"]

    print(text_to_translate)
    return jsonify({"translation": text_to_translate}), 200

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    print("Request received")
    text = request.json["text"]
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    tts = text_to_speech_api(text)
    audio_fp = BytesIO(tts)

    return send_file(audio_fp, mimetype='audio/wav', as_attachment=True, download_name='tts.wav')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
