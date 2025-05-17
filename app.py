import os
from time import time
from fastapi import FastAPI, HTTPException, Form, BackgroundTasks, File, UploadFile, Request, Query
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
from threading import Lock
import yfinance as yf
from pymongo import MongoClient
import shortuuid
from ocr_service import extract_text_from_image
from PyPDF2 import PdfReader  # Add this import for PDF processing
from typing import List
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from typing import Literal
import pandas as pd


import requests

app = FastAPI()



class InputData(BaseModel):
    nifty: float
    rsi: float
    vix: float

class OutputData(BaseModel):
    signal: Literal["BUY CE", "BUY PE", "STRADDLE", "AVOID"]
    confidence: float
    reason: str



from kiteconnect import KiteConnect

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8888", "https://admirable-smakager-729141.netlify.app","https://inspireme.in"],
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
    try:
        data = await request.json()
        print("Received request data:", data)

        longUrl = data.get("longUrl")
        alias = data.get("alias")

        if not longUrl:
            print("Error: Long URL is required.")
            raise HTTPException(status_code=400, detail="Long URL is required.")

        if alias:
            print(f"Checking availability of custom alias: {alias}")
            if url_collection.find_one({"short_url": alias}):
                print("Error: Custom alias is already taken.")
                raise HTTPException(status_code=400, detail="Custom alias is already taken.")
            short_url = alias
        else:
            short_url = generate_short_url()
            print(f"Generated short URL: {short_url}")

        # Insert into database
        url_collection.insert_one({"long_url": longUrl, "short_url": short_url})
        print(f"Inserted into DB: long_url={longUrl}, short_url={short_url}")
        return {"shortUrl": f"https://admirable-smakager-729141.netlify.app/{short_url}"}
    except Exception as e:
        print("Error in shorten_url:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")


# === Debug Routes Endpoint ===
@app.get("/debug/routes/")
async def list_routes():
    return [{"path": route.path, "name": route.name} for route in app.router.routes]



@app.post("/pdf-to-text/")
async def pdf_to_text(file: UploadFile = File(...)):
    """Extract text from an uploaded PDF file."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF.")

    try:
        # Save the uploaded PDF file temporarily
        temp_pdf_path = f"temp_{file.filename}"
        with open(temp_pdf_path, "wb") as temp_pdf_file:
            temp_pdf_file.write(await file.read())

        # Extract text from the PDF
        pdf_reader = PdfReader(temp_pdf_path)
        extracted_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])

        # Clean up temporary file
        os.remove(temp_pdf_path)

        # Return the extracted text as a plain text file
        return StreamingResponse(
            iter([extracted_text.encode("utf-8")]),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=extracted_text.txt"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")
        
        
        
        
@app.get("/preorderstocks")
async def preorder_stocks(current_time: str = Query(default=datetime.now().strftime('%H:%M'))):
    
      # Get current time in IST
    ist_now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%H:%M')

   # if not ("09:00" <= ist_now <= "09:15"):
      #  return {"status": "outside_preorder_time", "message": "This API only works between 09:00 and 09:15"}

    

    if not access_token_global:
        raise HTTPException(status_code=401, detail="Please authenticate first via /login")

    try:
        # Sample list of quality stocks
        symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
        exchange = "NSE"

        instrument_tokens = [f"{exchange}:{sym}" for sym in symbols]
        quotes = kite.quote(instrument_tokens)

        result = []
        for token in instrument_tokens:
            data = quotes[token]
            depth = data.get("depth", {})
            buy_orders = depth.get("buy", [])
            sell_orders = depth.get("sell", [])

            if not buy_orders or not sell_orders:
                continue

            top_buy = buy_orders[0]
            top_sell = sell_orders[0]

            buy_price = top_buy["price"]
            buy_qty = top_buy["quantity"]
            sell_price = top_sell["price"]
            sell_qty = top_sell["quantity"]

            price_diff = sell_price - buy_price
            price_diff_percent = (price_diff / buy_price) * 100

            if buy_qty > sell_qty and price_diff_percent >= 1:
                result.append({
                    "symbol": token,
                    "buy_price": buy_price,
                    "buy_qty": buy_qty,
                    "sell_price": sell_price,
                    "sell_qty": sell_qty,
                    "price_diff_percent": round(price_diff_percent, 2)
                })

        return {
            "status": "success",
            "stocks": result,
            "timestamp": ist_now
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock data: {e}")


        


API_KEY = "n6b5ozc4aoq2dfp9"          # replace with actual
API_SECRET = "dq9sbkgnlwt2qk52kfrbii7e1h5s19by"    # replace with actual

kite = KiteConnect(api_key=API_KEY)
access_token_global = None

@app.get("/login")
def login_redirect():
    login_url = kite.login_url()
    return {"login_url": login_url}

@app.get("/login/callback")
def login_callback(request_token: str):
    global access_token_global
    try:
        data = kite.generate_session(request_token, api_secret=API_SECRET)
        access_token_global = data["access_token"]
        kite.set_access_token(access_token_global)
        return {"message": "Login successful", "access_token": access_token_global}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/indicators")
def get_indicators():
    try:
        nifty = yf.Ticker("^NSEI")
        vix = yf.Ticker("^INDIAVIX")

        # Fetch historical data
        hist = nifty.history(period="20d", interval="1d")
        if hist.empty or "Close" not in hist.columns:
            return {"error": "Failed to fetch NIFTY data. Try again later."}

        delta = hist["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.dropna().iloc[-1]

        current_nifty = hist["Close"].iloc[-1]

        # VIX
        vix_hist = vix.history(period="5d", interval="1d")
        if vix_hist.empty:
            return {"error": "Failed to fetch India VIX."}
        current_vix = vix_hist["Close"].dropna().iloc[-1]

        return {
            "nifty": round(current_nifty, 2),
            "rsi": round(current_rsi, 2),
            "vix": round(current_vix, 2)
        }

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

@app.post("/api/signal", response_model=OutputData)
def predict_trade(data: InputData):
    nifty = data.nifty
    rsi = data.rsi
    vix = data.vix

    if rsi > 70 and vix < 13:
        return OutputData(signal="BUY PE", confidence=82.5, reason="Overbought RSI, low volatility")
    elif rsi < 30 and vix < 13:
        return OutputData(signal="BUY CE", confidence=80.1, reason="Oversold RSI, likely bounce")
    elif vix > 18:
        return OutputData(signal="STRADDLE", confidence=76.0, reason="High VIX, expect wide movement")
    else:
        return OutputData(signal="AVOID", confidence=55.0, reason="No clear signal")

@app.get("/oe")
def root():
    return {"status": "OptionEdge API running"}





@app.post("/generate-hindi-audio/")
async def generate_hindi_audio(request: Request):
    body = await request.json()
    response = requests.post(
        "https://audio.dubverse.ai/api/tts",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "DQOaqGwPE3ekDeNIocrtty3vKpuQd4dP"
        },
        json=body,
        stream=True
    )
    return StreamingResponse(response.raw, media_type="audio/mpeg")



@app.get("/{short_url}")
async def redirect_to_long_url(short_url: str):
    try:
        print(f"Looking up short URL: {short_url}")
        result = url_collection.find_one({"short_url": short_url})
        if not result:
            print(f"Error: Short URL not found for {short_url}")
            raise HTTPException(status_code=404, detail="Short URL not found.")

        long_url = result["long_url"]
        print(f"Redirecting to long URL: {long_url}")
        return RedirectResponse(url=long_url)
    except Exception as e:
        print("Error in redirect_to_long_url:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")
        
