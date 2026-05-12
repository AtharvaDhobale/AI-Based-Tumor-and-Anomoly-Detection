from fastapi import APIRouter

from app.api.routes import auth, mri, analysis


api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(mri.router)
api_router.include_router(analysis.router)

