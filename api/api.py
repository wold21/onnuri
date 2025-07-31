from fastapi import APIRouter
from api.endpoints import account

api_router = APIRouter()

api_router.include_router(account.router, prefix="/accounting", tags=["회계"])