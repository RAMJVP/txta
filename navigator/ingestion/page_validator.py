from navigator.security.url_allowlist import canonicalize,is_safe_internal_url
def validate_page(fetch_url,canonical,status='published'):
    url=canonical or fetch_url
    if status!='published' or not is_safe_internal_url(url): raise ValueError('page not eligible')
    return canonicalize(url)
