from navigator.security.url_allowlist import is_safe_internal_url
class UrlPolicyService:
    def filter(self,rows): return [r for r in rows if is_safe_internal_url(r.get('url') or r.get('canonicalUrl',''))]
