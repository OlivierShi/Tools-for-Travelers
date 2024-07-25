const recordZhButton = document.getElementById('recordZhButton');
const recordRuButton = document.getElementById('recordRuButton');
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
let recordLanguage = 'zh';
let targetLanguage = 'ru';

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

recordZhButton.addEventListener('mousedown', () => {
    recordLanguage = 'zh';
    targetLanguage = 'ru';
    currentUUID = uuid.v4(); // Generate a new UUID for this recording session
    mediaRecorder.start();
});

recordZhButton.addEventListener('mouseup', () => {
    srButton.disabled = false;
    mediaRecorder.stop();
});

recordZhButton.addEventListener('touchstart', () => {
    recordLanguage = 'zh';
    targetLanguage = 'ru';
    currentUUID = uuid.v4(); // Generate a new UUID for this recording session    
    mediaRecorder.start();
});

recordZhButton.addEventListener('touchend', () => {
    srButton.disabled = false;
    mediaRecorder.stop();
});

recordRuButton.addEventListener('mousedown', () => {
    recordLanguage = 'ru';
    targetLanguage = 'zh';
    currentUUID = uuid.v4(); // Generate a new UUID for this recording session
    mediaRecorder.start();
});

recordRuButton.addEventListener('mouseup', () => {
    srButton.disabled = false;
    mediaRecorder.stop();
});

recordRuButton.addEventListener('touchstart', () => {
    recordLanguage = 'ru';
    targetLanguage = 'zh';
    currentUUID = uuid.v4(); // Generate a new UUID for this recording session    
    mediaRecorder.start();
});

recordRuButton.addEventListener('touchend', () => {
    srButton.disabled = false;
    mediaRecorder.stop();
});

playButton.addEventListener('click', () => {
    audioPlayback.play();
});

srButton.addEventListener('click', () => {
    if (audioBlob) {
        fetch(endpoint + '/translator/api/sr', {
            method: 'POST',
            headers: {
                'Content-Type': 'audio/webm',
                'Recording-UUID': currentUUID,
                'lang': recordLanguage
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
    const textToTranslate = srResult.textContent.trim(); // Retrieve the editable text
    if (textToTranslate) {
        fetch(endpoint + '/translator/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Recording-UUID': currentUUID,
                'lang': recordLanguage
            },
            body: JSON.stringify({ text: textToTranslate })
        })
        .then(response => response.json())
        .then(result => {
            const translations = result.translations;
            const mainTranslation = translations.find(t => t.to === targetLanguage);
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
        fetch(endpoint + '/translator/api/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Recording-UUID': currentUUID,
                'lang': targetLanguage
            },
            body: JSON.stringify({ text: textToSpeak })
        })
        .then(response => response.blob())
        .then(blob => {
            const audioUrl = URL.createObjectURL(blob);
            ttsPlayback.src = audioUrl;
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
    fetch(endpoint + '/translator/api/history')
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