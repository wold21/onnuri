import os
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from database.schema import init_tables
import uvicorn
from api.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시
    DB_PATH = "database/onnuri.db"
    if not os.path.exists(DB_PATH):
        init_tables(DB_PATH)
    yield
    # 서버 종료 시 (필요시 정리 작업)

app = FastAPI(
    title="Onnuri API Server",
    description="Onnuri 과제 API 서버",
    version="1.0.0",
    docs_url="/docs",
    openapi_tags=[
        {"name": "회계", "description": "회계 API"}
    ],
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1", tags=["회계"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True
    )
