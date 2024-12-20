import os
from time import time
from fastapi import FastAPI, HTTPException, Form, BackgroundTasks, File, UploadFile, Request
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
from threading import Lock
import yfinance as yf
from pymongo import MongoClient
import shortuuid
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

# MongoDB setup for URL shortening
MONGO_URI = "mongodb+srv://jeevanpatel:T2JU3z0R5CIl4fZd@cluster0.5mr34.mongodb.net/?retryWrites=true&w=majority"
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)  # Update with your connection string
    db = client["url_shortener"]
    url_collection = db["urls"]
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")

# In-memory database for managing requests
request_db = {}
lock = Lock()

# Constants
REQUEST_LIMIT_TIME = 86400  # 24 hours in seconds
AUDIO_EXPIRY_TIME = 1800    # 30 minutes in seconds

# === Helper Functions ===
def cleanup_audio_file(file_path: str):
    """Delete audio file after expiry."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                pass  # Test if the file is accessible
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")

def generate_short_url():
    """Generate a random short URL."""
    return shortuuid.ShortUUID().random(length=6)

# === Audio Generation Endpoints ===
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
                raise HTTPException(status_code=429, detail="Only one request per device per day.")
        request_db[device_id] = {"timestamp": current_time}

    try:
        tts = gTTS(text)
        audio_file = f"{device_id}_{int(current_time)}.mp3"
        audio_path = os.path.join("temp_audio", audio_file)
        os.makedirs("temp_audio", exist_ok=True)
        tts.save(audio_path)
        background_tasks.add_task(cleanup_audio_file, audio_path)
        return StreamingResponse(
            open(audio_path, "rb"),
            media_type="audio/mpeg",
            headers={"Content-Disposition": f"attachment; filename={audio_file}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing your request: {e}")

@app.post("/generate-audio-hin/")
async def generate_audio_hindi(device_id: str = Form(...), text: str = Form(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    if not device_id.strip():
        raise HTTPException(status_code=400, detail="Device ID is required")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        tts = gTTS(text, lang='hi')
        audio_file = f"{device_id}_{int(time())}.mp3"
        audio_path = os.path.join("temp_audio", audio_file)
        os.makedirs("temp_audio", exist_ok=True)
        tts.save(audio_path)
        background_tasks.add_task(cleanup_audio_file, audio_path)
        return StreamingResponse(
            open(audio_path, "rb"),
            media_type="audio/mpeg",
            headers={"Content-Disposition": f"attachment; filename={audio_file}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing your request: {e}")

# === Text Extraction Endpoint ===
@app.post("/extract-text/")
async def extract_text(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "application/pdf", "image/heic"]:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    try:
        text = extract_text_from_image(file)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {e}")

# === Financial Data Endpoints ===
def fetch_nifty_index():
    try:
        nifty = yf.Ticker("^NSEI")
        data = nifty.history(period="1d")
        return round(data['Close'].iloc[-1], 2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Nifty Index: {e}")

def fetch_vix():
    try:
        vix = yf.Ticker("^INDIAVIX")
        data = vix.history(period="1d")
        return round(data['Close'].iloc[-1], 2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching VIX: {e}")

@app.get("/financial-data/")
async def get_financial_data():
    try:
        return {
            "status": "success",
            "data": {
                "Nifty Index": fetch_nifty_index(),
                "India VIX": fetch_vix(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

@app.post("/shorten")
async def shorten_url(request: Request):
    data = await request.json()
    longUrl = data.get("longUrl")
    alias = data.get("alias")

    if not longUrl:
        raise HTTPException(status_code=400, detail="Long URL is required.")

    if alias:
        if url_collection.find_one({"short_url": alias}):
            raise HTTPException(status_code=400, detail="Custom alias is already taken.")
        short_url = alias
    else:
        short_url = generate_short_url()

    url_collection.insert_one({"long_url": longUrl, "short_url": short_url})
    return {"shortUrl": f"http://localhost:8000/{short_url}"}

@app.get("/{short_url}")
async def redirect_to_long_url(short_url: str):
    result = url_collection.find_one({"short_url": short_url})
    if not result:
        raise HTTPException(status_code=404, detail="Short URL not found.")
    return RedirectResponse(url=result["long_url"])

# === Debug Routes Endpoint ===
@app.get("/debug/routes/")
async def list_routes():
    return [{"path": route.path, "name": route.name} for route in app.router.routes]
