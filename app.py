import os
import io
from time import time
from fastapi import FastAPI, HTTPException, Form, BackgroundTasks,File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
from threading import Lock
from ocr_service import extract_text_from_image



# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8888", "https://admirable-smakager-729141.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory database for managing requests
request_db = {}
lock = Lock()

# Constants
REQUEST_LIMIT_TIME = 86400  # 24 hours in seconds
AUDIO_EXPIRY_TIME = 1800    # 30 minutes in seconds

def cleanup_audio_file(file_path: str):
    """Delete audio file after expiry."""
    try:
        if os.path.exists(file_path):
            # Ensure the file is not in use before deleting
            with open(file_path, 'rb') as f:
                pass  # Test if the file is accessible
            os.remove(file_path)
    except PermissionError as e:
        print(f"PermissionError: Unable to delete file {file_path}. Error: {e}")
    except Exception as e:
        print(f"Error: Unable to delete file {file_path}. Error: {e}")


@app.post("/generate-audio/")
async def generate_audio(device_id: str = Form(...), text: str = Form(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    if not device_id.strip():
        raise HTTPException(status_code=400, detail="Device ID is required")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    
    with lock:
        current_time = time()
        if device_id in request_db:
            last_request_time = request_db[device_id]["timestamp"]
            if current_time - last_request_time < REQUEST_LIMIT_TIME:
                raise HTTPException(status_code=429, detail="Only one request is allowed per device per day.")
        
        # Update request tracking
        request_db[device_id] = {"timestamp": current_time}

    try:
        # Generate audio file
        tts = gTTS(text)
        audio_file = f"{device_id}_{int(current_time)}.mp3"
        audio_path = os.path.join("temp_audio", audio_file)

        # Ensure temp_audio directory exists
        os.makedirs("temp_audio", exist_ok=True)
        tts.save(audio_path)

        # Schedule file cleanup after expiry
        background_tasks.add_task(cleanup_audio_file, audio_path)

        # Stream the audio file to the user
        return StreamingResponse(
            open(audio_path, "rb"),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename={audio_file}"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing your request: {e}")




@app.post("/extract-text/")
async def extract_text(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "application/pdf", "image/heic"]:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    
    try:
        text = extract_text_from_image(file)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {e}")
