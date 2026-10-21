from fastapi import APIRouter, Request
router=APIRouter()
@router.get('/health')
async def health(): return {'status':'ok'}
@router.get('/ready')
async def ready(request:Request):
    if request.app.state.db is None: return {'status':'not_ready'}
    try: await request.app.state.db.command('ping'); return {'status':'ready'}
    except Exception: return {'status':'not_ready'}
