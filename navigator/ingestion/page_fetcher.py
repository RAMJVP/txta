import httpx
from navigator.security.url_allowlist import is_safe_internal_url
async def fetch_page(url:str,timeout=10,max_bytes=2_000_000):
    if not is_safe_internal_url(url): raise ValueError('external URL')
    async with httpx.AsyncClient(timeout=timeout,follow_redirects=False,headers={'User-Agent':'InspireMeNavigatorBot/1.0'}) as c:
        r=await c.get(url)
        if 300<=r.status_code<400:
            loc=r.headers.get('location','')
            if not is_safe_internal_url(loc): raise ValueError('external redirect')
            r=await c.get(loc)
        r.raise_for_status(); data=r.content[:max_bytes]
        return str(r.url),data.decode(r.encoding or 'utf-8',errors='replace')
