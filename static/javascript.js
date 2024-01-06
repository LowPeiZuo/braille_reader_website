let imageRatio;

async function postImage() {
    const fileInput = document.getElementById('upload_image');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select an image file');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('image', file);

        const response = await fetch("/detect", {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const responseData = await response.json();
        // console.log(responseData);
        
        if (!responseData.success) {
            throw new Error(responseData.error)
        }

        document.getElementById("detected_text").textContent = responseData.message;
        displayNamesOnCanvas(JSON.parse(responseData.positions), responseData.y_diff);

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        // Clear the file input after a successful upload
        document.getElementById('upload_image').value = "";
    }
}

function replaceImage() {
    const fileInput = document.getElementById('upload_image');
    const file = fileInput.files[0];

    const canvas = document.getElementById('result_image');
    const ctx = canvas.getContext('2d');
    
    if (!file) {
        canvas.innerHTML = ""; 
        return;
    }
    
    const imageUrl = URL.createObjectURL(file);
    const img = new Image();
    img.onload = function() {
        // Calculate the aspect ratio of the image
        const aspectRatio = img.width / img.height;

        // Calculate the maximum width and height based on the constraints
        const maxWidth = 60 * window.innerWidth / 100;
        const maxHeight = 40 * window.innerHeight / 100;

        // Calculate the actual width and height to fit within the constraints
        let newWidth = img.width;
        let newHeight = img.height;

        if (newWidth > maxWidth) {
            newWidth = maxWidth;
            newHeight = newWidth / aspectRatio;
        }

        if (newHeight > maxHeight) {
            newHeight = maxHeight;
            newWidth = newHeight * aspectRatio;
        }

        imageRatio = img.width / newWidth;

        // Set the canvas width and height
        canvas.width = newWidth;
        canvas.height = newHeight;
        // Draw the image on the canvas
        ctx.drawImage(img, 0, 0, newWidth, newHeight);
    };
    img.src = imageUrl;
}

// Function to display names on the canvas
function displayNamesOnCanvas(positions, y_diff) {
    const canvas = document.getElementById('result_image');
    const ctx = canvas.getContext('2d');

    ctx.strokeStyle = "#00FF00";
    ctx.lineWidth = 3;
    ctx.font = `${Math.floor(y_diff / 4)}px serif`;
    ctx.fillStyle = "#000000";

    for (let point of positions) {
        ctx.fillText(point.name, point.x / imageRatio , point.y / imageRatio + y_diff / 4);
    }
}

async function textToSpeech() {
    try {
        const text = document.getElementById('detected_text').value
        console.log(text.replaceAll("\n", " "))

        // const send_data = {
        //     text: text
        // }

        const response = await fetch("/voice", {
            method: 'POST',
            body: JSON.stringify(text),
            headers: {
                'Content-Type': 'application/json'
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        // Create an <audio> element to play the received audio
        const audioPlayer = new Audio(URL.createObjectURL(await response.blob()));

        // Play the audio
        audioPlayer.play();
    } catch (error) {
        console.error('Error:', error.message);
    } 
}