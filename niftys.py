from fastapi import FastAPI, HTTPException
import yfinance as yf
import requests
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup

# Initialize FastAPI app
app = FastAPI()


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8888", "https://admirable-smakager-729141.netlify.app"],  # Update as needed for specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def fetch_nifty_index():
    try:
        # Fetch Nifty 50 data using yfinance
        nifty = yf.Ticker("^NSEI")
        data = nifty.history(period="1d")
        last_price = data['Close'].iloc[-1]
        return round(last_price, 2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Nifty Index: {e}")

def fetch_vix():
    try:
        # Fetch India VIX using yfinance
        vix = yf.Ticker("^INDIAVIX")
        data = vix.history(period="1d")
        last_price = data['Close'].iloc[-1]
        return round(last_price, 2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching VIX: {e}")

def fetch_pe():
    try:
        # Scrape PE Ratio from NSE or other sources
        url = "https://www.nseindia.com/market-data/indices-overview"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        pe_value = soup.find('span', text="P/E Ratio").find_next('span').text
        return float(pe_value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching PE Ratio: {e}")

def fetch_pcr():
    try:
        # Fetch PCR (Put/Call Ratio) for Nifty options
        url = "https://www.nseindia.com/option-chain"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Add logic for PCR extraction here
        return "PCR calculation requires data parsing logic"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching PCR: {e}")

def fetch_cpi():
    try:
        # Fetch latest CPI from government sources or World Bank API
        url = "https://www.worldbank.org/en/indicator/FP.CPI.TOTL"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Parse CPI from the source
        return "CPI data parsing logic needed"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching CPI: {e}")

@app.get("/financial-data/")
async def get_financial_data():
    """
    Endpoint to fetch financial data for Nifty Index, India VIX, PE Ratio, PCR, and CPI.
    """
    try:
        data = {
            "Nifty Index": fetch_nifty_index(),
            "India VIX": fetch_vix(),
      #      "PE Ratio": fetch_pe(),
        #    "Put-Call Ratio (PCR)": fetch_pcr(),
         #   "Consumer Price Index (CPI)": fetch_cpi(),
        }
        return {"status": "success", "data": data}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
