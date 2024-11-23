import os
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io

from gtts import gTTS



app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8888", "https://admirable-smakager-729141.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the project root folder
project_root = os.path.dirname(os.path.abspath(__file__))





@app.post("/generate-audio/")
async def generate_audio(text: str = Form(...)):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    try:
        tts = gTTS(text)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return StreamingResponse(audio_buffer, media_type="audio/mpeg", headers={
            "Content-Disposition": "attachment; filename=output.mp3"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


