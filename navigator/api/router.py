from fastapi import APIRouter
from navigator.api.routes import search,sessions,events,health,admin
router=APIRouter(prefix='/api/navigator')
for r in (search.router,sessions.router,events.router,health.router,admin.router): router.include_router(r)
