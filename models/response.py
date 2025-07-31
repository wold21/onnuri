from typing import Any, Dict, Optional
from fastapi import HTTPException
from pydantic import BaseModel

class ResponseModel(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

def success_response(data: Any = None, message: str = "success") -> Dict[str, Any]:
    response = {
        "status": 200,
        "message": message
    }
    if data is not None:
        response["data"] = data
    
    return response

def error_response(status_code: int, error_message: str) -> HTTPException:
    detail = {
        "status": status_code,
        "message": "failure",
    }
    
    if error_message:
        detail["error"] = error_message
    
    return HTTPException(
        status_code=status_code,
        detail=detail
    )