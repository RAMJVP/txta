import os
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import pyttsx3
import io

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
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text is required")

        # Initialize pyttsx3 for text-to-speech
        engine = pyttsx3.init()

        # Path to save the audio file in the project root
        output_file_path = os.path.join(project_root, "output.mp3")

        # Save speech to the output.mp3 file
        engine.save_to_file(text, output_file_path)
        engine.runAndWait()

        # Read the audio file content
        with open(output_file_path, "rb") as audio_file:
            audio_content = audio_file.read()

        # Return the audio as a downloadable file
        return StreamingResponse(io.BytesIO(audio_content), media_type="audio/mp3", headers={
            "Content-Disposition": f"attachment; filename=output.mp3"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
