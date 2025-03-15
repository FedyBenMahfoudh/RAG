from fastapi import APIRouter,Depends
import os
from helpers.config import get_settings, Settings
base_router = APIRouter(prefix="/model/v1",tags=["model-v1"])
@base_router.get("/")
async def root(app_settings: Settings = Depends(get_settings)):
    app_name = app_settings.APP_NAME  # Ajout d'une valeur par défaut si la variable n'existe pas.
    app_version = app_settings.APP_VERSION  # Même chose ici.
    return {
        "message": "Welcome to RAG API",
        "app_name": app_name,
        "app_version": app_version
    }
