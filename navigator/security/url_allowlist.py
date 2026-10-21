from urllib.parse import urlparse, urljoin
ALLOWED={'inspireme.in','www.inspireme.in'}
def is_safe_internal_url(url:str)->bool:
    if not url or any(c in url for c in ['\r','\n','\\']): return False
    if url.startswith('/') and not url.startswith('//'): return True
    p=urlparse(url)
    return p.scheme=='https' and p.hostname in ALLOWED and not p.username and not p.password

def canonicalize(url:str)->str:
    full=urljoin('https://inspireme.in',url); p=urlparse(full)
    if p.hostname not in ALLOWED or p.scheme!='https': raise ValueError('external url')
    path=p.path.rstrip('/') or '/'
    return f'https://inspireme.in{path}' + (f'?{p.query}' if p.query else '')
