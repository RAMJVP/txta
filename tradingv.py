from bs4 import BeautifulSoup
import requests

# URL to scrape
url = "https://in.tradingview.com/symbols/NSE-NIFTY/technicals/"

# Send request and parse the response
response = requests.get(url)
if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")

    # Debugging: Print soup to verify content
    #print(soup.prettify())  # Optional: Remove this after verifying content

    # Look for the container using a flexible match
    #countersWrapper-kg4MJrFB
    #speedometerWrapper-kg4MJrFB summary-kg4MJrFB tabletVertical-kg4MJrFB
    container = soup.find('div', class_=lambda c: c and 'countersWrapper' in c)
    
    if container:
        summary_score = container.text
        print(f"Summary Score: {summary_score}")
    else:
        print("Error: speedometersContainer not found")
else:
    print(f"Failed to fetch the page. Status code: {response.status_code}")
