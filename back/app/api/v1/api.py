from fastapi import APIRouter

from app.api.v1.endpoints import auth, caracterizacion, catalogos, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(catalogos.router, tags=["catalogos"])
api_router.include_router(caracterizacion.router, tags=["caracterizacion-upgd"])
