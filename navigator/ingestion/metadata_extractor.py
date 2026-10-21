from bs4 import BeautifulSoup
def extract_metadata(html:str):
    s=BeautifulSoup(html,'html.parser'); title=(s.title.string.strip() if s.title and s.title.string else '')
    desc=s.find('meta',attrs={'name':'description'}); kw=s.find('meta',attrs={'name':'keywords'}); canon=s.find('link',rel='canonical')
    return {'title':title,'description':desc.get('content','').strip() if desc else '','keywords':[x.strip() for x in kw.get('content','').split(',') if x.strip()] if kw else [],'headings':[h.get_text(' ',strip=True) for h in s.find_all(['h1','h2','h3'])][:50],'canonical':canon.get('href') if canon else None}
