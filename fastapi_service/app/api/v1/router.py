from fastapi import APIRouter

from app.api.v1.endpoints import generate, upload

api_router = APIRouter()
api_router.include_router(upload.router, tags=["code"])
api_router.include_router(generate.router, tags=["generation"])
