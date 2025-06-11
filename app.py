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
from typing import List


from yt_trends_utils import get_recent_video_captions, get_google_trends_for_india

import pandas as pd
import numpy as np

import requests
import pytz
from datetime import date
from datetime import datetime, timedelta





import json
import random
from fastapi.responses import JSONResponse





class StrategyInput(BaseModel):
    nifty: float
    rsi: float
    vix: float
    event: str

class StrategyOutput(BaseModel):
    strategy: str
    confidence: float
    reason: str


    
SAVE_FILE = "saved_inputs.json"



class InputData(BaseModel):
    nifty: float
    rsi: float
    vix: float

class OutputData(BaseModel):
    signal: str
    confidence: float
    reason: str

class BacktestResult(BaseModel):
    date: str
    nifty: float
    rsi: float
    vix: float
    signal: str
    confidence: float
    reason: str
    simulated_return: float

class BacktestResponse(BaseModel):
    trades: List[BacktestResult]
    win_rate: float
    avg_return: float
    total_return: float

# Sample rule-based event calendar
EVENTS = [
    {"date": "2025-06-13", "event": "Weekly Expiry", "impact": "High"},
    {"date": "2025-06-15", "event": "Fed Interest Rate Decision", "impact": "High"},
    {"date": "2025-06-18", "event": "India GDP Data", "impact": "Medium"},
    {"date": "2025-07-01", "event": "Union Budget", "impact": "Very High"},
    {"date": "2025-07-15", "event": "General Elections Result Day", "impact": "Extreme"},
]

class CalendarEvent(BaseModel):
    date: str
    event: str
    impact: str


class InputData(BaseModel):
    nifty: float
    rsi: float
    vix: float

class OutputData(BaseModel):
    signal: Literal["BUY CE", "BUY PE", "STRADDLE", "AVOID"]
    confidence: float
    reason: str

class OHLCVInput(BaseModel):
    data: list  # list of dicts: [{"timestamp": ..., "open": 21500 "high": ..., "low": ..., "close": ..., "volume": ...}] # Not used, but required for POST schema compatibility



class OHLCVInput(BaseModel):
    data: list
    
    

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

        hist = nifty.history(period="20d", interval="1d")
        if hist.empty or "Close" not in hist.columns:
            raise Exception("NIFTY history is empty")

        delta = hist["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.dropna().iloc[-1]
        current_nifty = hist["Close"].iloc[-1]

        vix_hist = vix.history(period="5d", interval="1d")
        if vix_hist.empty:
            raise Exception("VIX history is empty")
        current_vix = vix_hist["Close"].dropna().iloc[-1]

        print("Fetched live indicators")
        return {
            "nifty": round(current_nifty, 2),
            "rsi": round(current_rsi, 2),
            "vix": round(current_vix, 2)
        }

    except Exception as e:
        print(f"Live fetch failed: {e}")
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r") as f:
                    saved_data = json.load(f)
                    print("Returning values from saved file:", saved_data)
                    return saved_data
            except Exception as err:
                print(f"Failed to read saved file: {err}")

        fallback = {
            "nifty": 25120.00,
            "rsi": 70.34,
            "vix": 14.86,
            "note": "Live data fetch failed. Showing fallback values."
        }
        print("Returning fallback values:", fallback)
        return fallback





@app.get("/api/indicators/saved")
def get_saved_indicators():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            print("Loaded saved indicators:", data)
            return data
    return {"nifty": 25120.00, "rsi": 70.34, "vix": 14.86, "note": "No saved file found"}


@app.post("/api/indicators/save")
def save_indicators(data: InputData):
    try:
        print(f"[SAVE] Attempting to save indicators to file: {SAVE_FILE}")
        with open(SAVE_FILE, "w") as f:
            json.dump(data.dict(), f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        print(f"[SAVE] Successfully saved: {data.dict()}")
        return {"status": "saved", "data": data.dict()}
    except Exception as e:
        print(f"[SAVE ERROR] Failed to save indicators: {e}")
        raise HTTPException(status_code=500, detail="Failed to save indicators")



@app.get("/api/indicators/view-file")
def view_file_contents():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            contents = json.load(f)
        print("File content viewed:", contents)
        return contents
    return {"error": "File not found"}

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



def is_market_open_india() -> bool:
    india_tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india_tz)
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close



def fetch_intraday_yahoo(symbol="RELIANCE.NS"):
    ticker = yf.Ticker(symbol)
    df = ticker.history(interval="5m", period="1d")
    if df.empty:
        raise Exception("No intraday data from Yahoo")
    df.reset_index(inplace=True)
    df.rename(columns={"Datetime": "timestamp"}, inplace=True)
    return df


def fetch_nse_intraday(symbol="RELIANCE"):
    import time

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}",
    }

    session = requests.Session()
    try:
        # Hit the homepage to get valid cookies
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        time.sleep(1.5)

        # Updated API endpoint
        url = f"https://www.nseindia.com/api/chart-data?symbol={symbol}"
        res = session.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            raise Exception(f"NSE API error (HTTP {res.status_code})")

        data = res.json()
        candles = data.get("grapthData", [])
        if not candles:
            raise Exception("No intraday data from NSE API")

        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

    except Exception as e:
        raise Exception(f"Failed to fetch NSE data: {e}")





@app.post("/api/alerts/breakout")
async def get_alert(_: Request):
    if not is_market_open_india():
        return {
            "type": None, "volumeSpike": False, "pattern": None, "confidence": 0,
            "error": "Market is closed"
        }

    try:
        df = fetch_intraday_yahoo("RELIANCE")
        if len(df) < 3:
            raise Exception("Too little data")

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        breakout = bool(latest["close"] > df["high"][:-1].max())
        breakdown = bool(latest["close"] < df["low"][:-1].min())
        df["vol_ma20"] = df["volume"].rolling(20).mean()
        volume_spike = latest["volume"] > 1.5 * df["vol_ma20"].iloc[-1]

        pattern = None
        if latest["close"] > latest["open"] and prev["close"] < prev["open"]:
            if latest["close"] > prev["open"] and latest["open"] < prev["close"]:
                pattern = "Bullish Engulfing"

        result = {
            "type": None, "volumeSpike": volume_spike,
            "pattern": pattern, "confidence": 0
        }

        if breakout and volume_spike:
            result["type"] = "breakout"
            result["confidence"] = 90 if pattern else 75
        elif breakdown and volume_spike:
            result["type"] = "breakdown"
            result["confidence"] = 90 if pattern else 75

        return result

    except Exception as e:
        return {
            "type": None, "volumeSpike": False, "pattern": None, "confidence": 0,
            "error": f"NSE fetch failed: {str(e)}"
        }
        
      
      

@app.get("/api/option_suggestions")
def get_option_suggestions():
    try:
        nifty = yf.Ticker("^NSEI")
        vix = yf.Ticker("^INDIAVIX")

        # Fetch historical data
        hist = nifty.history(period="20d", interval="1d")
        if hist.empty or "Close" not in hist.columns:
            return {"error": "Failed to fetch NIFTY data. Try again later."}

        # RSI Calculation
        delta = hist["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.dropna().iloc[-1]

        current_nifty = hist["Close"].iloc[-1]

        # VIX Calculation
        vix_hist = vix.history(period="5d", interval="1d")
        if vix_hist.empty:
            return {"error": "Failed to fetch India VIX."}
        current_vix = vix_hist["Close"].dropna().iloc[-1]

        # Option Suggestions
        if current_vix > 18 and current_rsi > 70:
            suggestion = f"Try {round(current_nifty + 100, 0)} CE + {round(current_nifty - 100, 0)} PE"
        else:
            suggestion = "Conditions not met for a straddle/strangle suggestion."

        return {
            "nifty": round(current_nifty, 2),
            "rsi": round(current_rsi, 2),
            "vix": round(current_vix, 2),
            "suggestion": suggestion
        }

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}






@app.get("/api/youtube-captions")
def fetch_youtube_captions(max_results: int = 10):
    try:
        data = get_recent_video_captions(max_results)
        return {"status": "success", "videos": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/google-trends")
def fetch_google_trends():
    try:
        trends = get_google_trends_for_india()
        return {"status": "success", "trends": trends}
    except Exception as e:
        print("[INFO] Falling back to realtime_trending_searches()...")
        return {"status": "error", "message": str(e)}




@app.get("/api/event-calendar", response_model=list[CalendarEvent])
def get_event_calendar():
    today = date.today().isoformat()
    upcoming_events = [event for event in EVENTS if event["date"] >= today]
    return upcoming_events



@app.post("/api/signal1", response_model=OutputData)
def predict_trade(data: InputData):
    if data.rsi > 70 and data.vix < 13:
        return OutputData(signal="BUY PE", confidence=82.5, reason="Overbought RSI, low volatility")
    elif data.rsi < 30 and data.vix < 13:
        return OutputData(signal="BUY CE", confidence=80.1, reason="Oversold RSI, likely bounce")
    elif data.vix > 18:
        return OutputData(signal="STRADDLE", confidence=76.0, reason="High VIX, expect wide movement")
    else:
        return OutputData(signal="AVOID", confidence=55.0, reason="No clear signal")


#If you only want to run today’s prediction (no historical backtest), you can simplify /api/backtest like this:
@app.post("/api/backtest")
def backtest():
    try:
        print("Fetching live indicators from /api/indicators...")
        indicators = requests.get("https://txta-1.onrender.com/api/indicators").json()

        n_val = indicators["nifty"]
        r_val = indicators["rsi"]
        v_val = indicators["vix"]
        print(f"Fetched: NIFTY={n_val}, RSI={r_val}, VIX={v_val}")

        signal_result = predict_trade(InputData(nifty=n_val, rsi=r_val, vix=v_val))
        print(f"Signal: {signal_result.signal}, Confidence: {signal_result.confidence}, Reason: {signal_result.reason}")

        trades = [BacktestResult(
            date=datetime.now().strftime("%Y-%m-%d"),
            nifty=n_val,
            rsi=r_val,
            vix=v_val,
            signal=signal_result.signal,
            confidence=signal_result.confidence,
            reason=signal_result.reason,
            simulated_return=2.0 if signal_result.signal in ["BUY CE", "STRADDLE"] else -1.0
        )]

        return BacktestResponse(
            trades=trades,
            win_rate=100.0 if trades[0].simulated_return > 0 else 0.0,
            avg_return=trades[0].simulated_return,
            total_return=trades[0].simulated_return
        )

    except Exception as e:
        print(f"Error in /api/backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategy", response_model=StrategyOutput)
def get_event_strategy(data: StrategyInput):
    event = data.event.lower().strip()
    rsi = data.rsi
    vix = data.vix

    if not event:
        return StrategyOutput(
            strategy="Manual Analysis Required",
            confidence=0.0,
            reason="No event selected. Please analyze based on indicators."
        )

    if event == "rbi":
        if rsi < 40:
            return StrategyOutput(
                strategy="Buy BANKNIFTY ATM CE (3 weeks)",
                confidence=87.5,
                reason="Dovish outlook + oversold condition"
            )
        else:
            return StrategyOutput(
                strategy="ATM Straddle on BANKNIFTY",
                confidence=75.0,
                reason="Neutral stance expected from RBI + low VIX"
            )

    elif event == "budget":
        if vix > 16:
            return StrategyOutput(
                strategy="Bear Put Spread on NIFTY",
                confidence=82.0,
                reason="Pre-budget volatility spike and uncertain fiscal cues"
            )
        else:
            return StrategyOutput(
                strategy="Buy NIFTY CE (ATM +1 week)",
                confidence=68.0,
                reason="Positive sentiment around budget announcement"
            )

    elif event == "usfed":
        return StrategyOutput(
            strategy="NIFTY ATM Strangle (exp +2 weeks)",
            confidence=78.5,
            reason="Fed day has historically caused wide swings in both directions"
        )

    elif event == "results":
        return StrategyOutput(
            strategy="Buy IT Sector CE Basket",
            confidence=74.3,
            reason="IT sector historically outperforms in earnings season (Q4)"
        )

    return StrategyOutput(
        strategy="AVOID",
        confidence=50.0,
        reason="No matching strategy for selected event"
    )




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
        



