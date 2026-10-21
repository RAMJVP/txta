import httpx
from xml.etree import ElementTree as ET
from navigator.security.url_allowlist import is_safe_internal_url
async def read_sitemap(url:str,timeout=10):
    if not is_safe_internal_url(url): raise ValueError('unsafe sitemap')
    async with httpx.AsyncClient(timeout=timeout,follow_redirects=False) as c:
        r=await c.get(url); r.raise_for_status(); root=ET.fromstring(r.content)
    urls=[n.text.strip() for n in root.findall('.//{*}loc') if n.text and is_safe_internal_url(n.text.strip())]
    return urls
