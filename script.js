const recordButton = document.getElementById('recordButton');
const playButton = document.getElementById('playButton');
const srButton = document.getElementById('srButton');
const audioPlayback = document.getElementById('audioPlayback');
const srResult = document.getElementById('srResult');

let mediaRecorder;
let audioChunks = [];

navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
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
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const reader = new FileReader();

    reader.onloadend = () => {
        const base64Audio = reader.result.split(',')[1];
        const data = { audio: base64Audio };

        fetch('/host/api/sr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            srResult.textContent = result.text;
        })
        .catch(error => {
            console.error('Error:', error);
        });
    };

    reader.readAsDataURL(audioBlob);
});
