from fastapi import APIRouter, Depends
from navigator.security.admin_auth import require_admin
router=APIRouter()
@router.post('/admin/reindex',dependencies=[Depends(require_admin)])
async def reindex(): return {'status':'accepted','message':'Run scripts/reindex_embeddings.py in deployment job.'}
