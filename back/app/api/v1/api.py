from fastapi import APIRouter

from app.api.v1.endpoints import auth, caracterizacion, catalogos, fichas_basicas, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(catalogos.router, tags=["catalogos"])
api_router.include_router(caracterizacion.router, tags=["caracterizacion-upgd"])
api_router.include_router(fichas_basicas.router, tags=["fichas-datos-basicos"])
