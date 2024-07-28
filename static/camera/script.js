let useFrontCamera = true;
let currentStream = null;

document.getElementById('start-camera').addEventListener('click', async function() {
    const video = document.getElementById('video');
    const takePhotoButton = document.getElementById('take-photo');
    const photo = document.getElementById('photo');
    const ocrResults = document.getElementById('ocr-results');

    // Hide the previously taken photo
    photo.style.display = 'none';
    ocrResults.style.display = 'none';

    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
    }

    const constraints = {
        video: {
            facingMode: useFrontCamera ? 'user' : 'environment'
        }
    };

    try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        currentStream = stream;
        video.srcObject = stream;
        video.style.display = 'block';
        takePhotoButton.style.display = 'block';
    } 
    catch (err) {
        console.error("Error accessing the camera: ", err);
    }
});

document.getElementById('switch-camera').addEventListener('click', async function() {
    useFrontCamera = !useFrontCamera;
    const switchCameraButton = document.getElementById('switch-camera');
    switchCameraButton.innerHTML = useFrontCamera ? '<i class="fas fa-sync-alt"></i>' : '<i class="fas fa-sync-alt"></i>';

    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
    }

    const constraints = {
        video: {
            facingMode: useFrontCamera ? 'user' : 'environment'
        }
    };

    try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        currentStream = stream;
        const video = document.getElementById('video');
        video.srcObject = stream;
    } catch (err) {
        console.error("Error switching the camera: ", err);
    }
});

document.getElementById('take-photo').addEventListener('click', async function() {
    const video = document.getElementById('video');
    const photo = document.getElementById('photo');
    const canvas = document.createElement('canvas');
    const ocrResults = document.getElementById('ocr-results');
    const ocrTableBody = document.getElementById('ocr-table-body');

    // Set canvas size to match video size
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw the current frame from the video onto the canvas
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);

    // Get the image data URL from the canvas
    const dataUrl = canvas.toDataURL('image/png');

    // Hide the video element
    video.style.display = 'none';

    // Display the captured photo temporarily
    photo.setAttribute('src', dataUrl);
    photo.style.display = 'block';

    try {
        // Convert data URL to Blob
        const response = await fetch(dataUrl);
        const blob = await response.blob();
        
        // Create a FormData object and append the image file
        const formData = new FormData();
        formData.append('file', blob, 'photo.png');

        // Post the image to the API
        const ocrResponse = await fetch(endpoint + '/camera/api/ocr', {
            method: 'POST',
            body: formData
        });

        // Check if the response is okay
        if (!ocrResponse.ok) {
            throw new Error('OCR API request failed');
        }

        // Get the new image URL from the OCR response
        const ocrResult = await ocrResponse.json();

        // Replace the original image with the new image from the OCR result
        photo.setAttribute('src', ocrResult.newImageUrl);

        // Clear previous OCR results
        ocrTableBody.innerHTML = '';

        // Populate the OCR results table
        ocrResult.ocr.forEach(row => {
            const tr = document.createElement('tr');
            const tdOcr = document.createElement('td');
            const tdTranslation = document.createElement('td');
            tdOcr.textContent = row[0];
            tdTranslation.textContent = row[1];
            tr.appendChild(tdOcr);
            tr.appendChild(tdTranslation);
            ocrTableBody.appendChild(tr);
        });

        // Display the OCR results
        ocrResults.style.display = 'block';
    } catch (err) {
        console.error('Error processing the photo:', err);
    }

    // Hide the take photo button
    document.getElementById('take-photo').style.display = 'none';
});
