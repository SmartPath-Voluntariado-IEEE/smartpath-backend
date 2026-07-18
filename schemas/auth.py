from pydantic import BaseModel
from typing import Dict, Any

class UserMeResponse(BaseModel):
    status: str
    message: str
    user_details: Dict[str, Any]