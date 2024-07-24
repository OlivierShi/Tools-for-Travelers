const recordButton = document.getElementById('recordButton');
const playButton = document.getElementById('playButton');
const srButton = document.getElementById('srButton');
const translateButton = document.getElementById('translateButton');
const ttsButton = document.getElementById('ttsButton');
const historyButton = document.getElementById('historyButton');

const audioPlayback = document.getElementById('audioPlayback');
const srResult = document.getElementById('srResult');
const translationMain = document.getElementById('translationMain');
const translationSupplement = document.getElementById('translationSupplement');
const ttsPlayback = document.getElementById('ttsPlayback');
const historyContainer = document.getElementById('historyContainer');

let mediaRecorder;
let audioChunks = [];
let audioBlob;
let currentUUID;

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
    currentUUID = uuid.v4(); // Generate a new UUID for this recording session
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
        fetch(endpoint + '/api/sr', {
            method: 'POST',
            headers: {
                'Content-Type': 'audio/webm',
                'Recording-UUID': currentUUID
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
        fetch(endpoint + '/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Recording-UUID': currentUUID
            },
            body: JSON.stringify({ text: textToTranslate })
        })
        .then(response => response.json())
        .then(result => {
            const translations = result.translations;
            const mainTranslation = translations.find(t => t.to === 'ru');
            const supplementTranslation = translations.find(t => t.to === 'en');

            translationMain.textContent = mainTranslation ? mainTranslation.text : '';
            translationSupplement.textContent = supplementTranslation ? supplementTranslation.text : '';

            ttsButton.disabled = !translationMain;
        })
        .catch(error => {
            console.error('Error:', error);
        });
    } else {
        console.error('No text to translate.');
    }
});

ttsButton.addEventListener('click', () => {
    const textToSpeak = translationMain.textContent;
    if (textToSpeak) {
        fetch(endpoint + '/api/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Recording-UUID': currentUUID
            },
            body: JSON.stringify({ text: textToSpeak })
        })
        .then(response => response.blob())
        .then(blob => {
            const audioUrl = URL.createObjectURL(blob);
            ttsPlayback.src = audioUrl;
            // ttsPlayback.style.display = 'block';
            ttsPlayback.play();
        })
        .catch(error => {
            console.error('Error:', error);
        });
    } else {
        console.error('No text to speak.');
    }
});

historyButton.addEventListener('click', () => {
    fetch(endpoint + '/api/history')
        .then(response => response.json())
        .then(history => {
            historyContainer.innerHTML = '';
            history.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.classList.add('history-item');
                historyItem.innerHTML = `<strong>${item.datetime}</strong><br>Chinese: ${item.Chinese}<br>Russian: ${item.Russian}<br>English: ${item.English}`;
                historyContainer.appendChild(historyItem);
            });
        })
        .catch(error => {
            console.error('Error fetching history:', error);
        });
});