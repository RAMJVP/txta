from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def fetch_all_urls(base_url):
    # Corrected WebDriver initialization
    service = Service('F:\\Program Files\\driver\\chrome-win64\\chrome.exe')  # Path to chromedriver
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(base_url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        urls = set()
        for link in soup.find_all('a', href=True):
            full_url = urljoin(base_url, link['href'])
            urls.add(full_url)
            
        return urls
    finally:
        driver.quit()

if __name__ == "__main__":
    website_url = 'https://admirable-smakager-729141.netlify.app/'
    urls = fetch_all_urls(website_url)
    
    print("Found URLs:")
    for url in urls:
        print(url)
