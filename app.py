from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig
from azure.storage.blob import BlobServiceClient
import uuid

from dotenv import load_dotenv

load_dotenv()
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")




app = FastAPI()

# CORS Configuration
origins = [
    "http://localhost:8888",
    "https://admirable-smakager-729141.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure Speech Service Config
SPEECH_KEY = "2L2Z57u9OKgtjcOlmDhvWyyzsSAOawiU5x7Vmasy3UNL36QEuAvBJQQJ99AKAC3pKaRXJ3w3AAAYACOGcCJK"
SERVICE_REGION = "eastasia"
speech_config = SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)

# Azure Blob Storage Config
BLOB_CONTAINER_NAME = "$logs"  # Create a container in your Storage Account

blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

@app.post("/generate-audio/")
async def generate_audio(text: str = Form(...)):
    try:
        # Generate a unique filename for the MP3 file
        file_name = f"{uuid.uuid4()}.mp3"
        local_file_path = f"/tmp/{file_name}"  # Temporary file storage on the server

        # Configure Azure Speech Synthesizer to save the file locally
        audio_output = AudioConfig(filename=local_file_path)
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)

        # Generate Speech
        synthesizer.speak_text_async(text).get()

        # Upload the file to Azure Blob Storage
        with open(local_file_path, "rb") as data:
            blob_client = container_client.get_blob_client(file_name)
            blob_client.upload_blob(data, overwrite=True)

        # Generate a SAS (Shared Access Signature) URL for the uploaded file
        download_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{BLOB_CONTAINER_NAME}/{file_name}"

        return {"message": "Audio generated successfully.", "download_url": download_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
