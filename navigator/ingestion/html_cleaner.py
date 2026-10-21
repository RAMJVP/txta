from bs4 import BeautifulSoup
def clean_html(html:str):
    soup=BeautifulSoup(html,'html.parser')
    for tag in soup(['script','style','noscript','iframe','nav','footer','form','svg']): tag.decompose()
    main=soup.find('main') or soup.find('article') or soup.body or soup
    return ' '.join(main.stripped_strings)
