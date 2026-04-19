from fastapi import APIRouter
from app.api.routes import mp, admin

api_router = APIRouter()
api_router.include_router(mp.router, prefix="/mp", tags=["mp"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
