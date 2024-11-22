from fastapi import FastAPI, HTTPException, Form
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig

app = FastAPI()

# Azure Speech Service Config
SPEECH_KEY = "2L2Z57u9OKgtjcOlmDhvWyyzsSAOawiU5x7Vmasy3UNL36QEuAvBJQQJ99AKAC3pKaRXJ3w3AAAYACOGcCJK"
SERVICE_REGION = "eastasia"  # e.g., "eastus"
speech_config = SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)

@app.post("/generate-audio/")
async def generate_audio(text: str = Form(...)):
    try:
        # Configure output to MP3
        audio_output = AudioConfig(filename="output.mp3")
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)

        # Generate Speech
        synthesizer.speak_text_async(text).get()
        return {"message": "Audio generated successfully.", "file_path": "output.mp3"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
