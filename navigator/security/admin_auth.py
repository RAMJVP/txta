from fastapi import Header, HTTPException
from navigator.core.config import get_settings
async def require_admin(x_admin_token:str|None=Header(default=None)):
    token=get_settings().admin_reindex_token
    if not token or x_admin_token!=token: raise HTTPException(status_code=401,detail='unauthorized')
