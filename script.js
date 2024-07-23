const recordButton = document.getElementById('recordButton');
const playButton = document.getElementById('playButton');
const srButton = document.getElementById('srButton');
const audioPlayback = document.getElementById('audioPlayback');
const srResult = document.getElementById('srResult');
const translationResult = document.getElementById('translationResult');
const ttsPlayback = document.getElementById('ttsPlayback');

let mediaRecorder;
let audioChunks = [];
let audioBlob;

navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            
            audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const audioUrl = URL.createObjectURL(audioBlob);
            audioPlayback.src = audioUrl;
            playButton.disabled = false;
            srButton.disabled = false;
            audioChunks = [];
        };
    })
    .catch(error => {
        console.error('Error accessing media devices.', error);
    });

recordButton.addEventListener('mousedown', () => {
    mediaRecorder.start();
});

recordButton.addEventListener('mouseup', () => {
    mediaRecorder.stop();
});

recordButton.addEventListener('touchstart', () => {
    mediaRecorder.start();
});

recordButton.addEventListener('touchend', () => {
    mediaRecorder.stop();
});

playButton.addEventListener('click', () => {
    audioPlayback.play();
});

srButton.addEventListener('click', () => {
    if (audioBlob) {
        fetch('http://100.64.145.60:5000/api/sr', {
            method: 'POST',
            headers: {
                'Content-Type': 'audio/webm'
            },
            body: audioBlob
        })
        .then(response => response.json())
        .then(result => {
            srResult.textContent = result.message;
            translateButton.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
        });
    } else {
        console.error('No audio recorded.');
    }
});

translateButton.addEventListener('click', () => {
    const textToTranslate = srResult.textContent;
    if (textToTranslate) {
        fetch('http://100.64.145.60:5000/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: textToTranslate })
        })
        .then(response => response.json())
        .then(result => {
            translationResult.textContent = result.translation;
            ttsButton.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
        });
    } else {
        console.error('No text to translate.');
    }
});

ttsButton.addEventListener('click', () => {
    const textToSpeak = translationResult.textContent;
    if (textToSpeak) {
        fetch('http://100.64.145.60:5000/api/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: textToSpeak })
        })
        .then(response => response.blob())
        .then(blob => {
            const audioUrl = URL.createObjectURL(blob);
            ttsPlayback.src = audioUrl;
            ttsPlayback.style.display = 'block';
            ttsPlayback.play();
        })
        .catch(error => {
            console.error('Error:', error);
        });
    } else {
        console.error('No text to speak.');
    }
});