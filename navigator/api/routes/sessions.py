from fastapi import APIRouter, Request
from navigator.api.dependencies import get_db
from navigator.repositories.session_repository import SessionRepository
from navigator.services.session_memory_service import SessionMemoryService
router=APIRouter()
@router.delete('/session/{session_id}',status_code=204)
async def clear_session(session_id:str,request:Request):
    await SessionMemoryService(SessionRepository(get_db(request))).clear(session_id)
