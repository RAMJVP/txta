from starlette.middleware.base import BaseHTTPMiddleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        r=await call_next(request)
        r.headers['X-Content-Type-Options']='nosniff'; r.headers['X-Frame-Options']='DENY'
        r.headers['Referrer-Policy']='same-origin'; r.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        r.headers['Content-Security-Policy']="default-src 'none'; frame-ancestors 'none'"
        return r
