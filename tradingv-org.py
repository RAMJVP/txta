import requests
from bs4 import BeautifulSoup

url = "https://in.tradingview.com/symbols/NSE-NIFTY/technicals/"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

print(f"Hello, ")  # Assuming response has a text attribute {response.text}


# Extract the summary score (you may need to adjust the selector based on the page structure)
summary_score = soup.find('div', {'class': 'speedometersContainer'}).text


print(summary_score)
