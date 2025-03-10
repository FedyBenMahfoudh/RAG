from fastapi import FastAPI,APIRouter

base_router = APIRouter(
    prefix="/model/v1",
    tags=["model-v1"],
)

@base_router.get("/")
async def root():
    return {"message": "Welcome to RAG API"}