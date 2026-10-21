from fastapi import APIRouter, Request
from navigator.schemas.navigator import LinkClickRequest
from navigator.repositories.click_event_repository import ClickEventRepository
router=APIRouter()
@router.post('/events/link-click',status_code=204)
async def link_click(payload:LinkClickRequest,request:Request): await ClickEventRepository(request.app.state.db).add(payload.requestId,payload.pageId)
