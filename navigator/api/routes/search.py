import asyncio
from fastapi import APIRouter, Depends, Request, HTTPException
from navigator.schemas.navigator import SearchRequest, SearchResponse
from navigator.api.dependencies import get_navigator_service
from navigator.core.config import get_settings
from navigator.security.rate_limiter import rate_limiter
router=APIRouter()
@router.post('/search',response_model=SearchResponse)
async def search(req:SearchRequest,request:Request,svc=Depends(get_navigator_service)):
    key=request.client.host if request.client else 'unknown'
    if not rate_limiter.allow(key): raise HTTPException(status_code=429,detail='rate limit exceeded')
    try: return await asyncio.wait_for(svc.search(req),timeout=get_settings().navigator_request_timeout_ms/1000)
    except asyncio.TimeoutError: return SearchResponse(requestId='timeout',status='temporary_error',message='Search timed out. Please try again.')
