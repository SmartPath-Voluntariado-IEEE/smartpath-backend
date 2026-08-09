from typing import Any

from pydantic import BaseModel


class UserMeResponse(BaseModel):
    status: str
    message: str
    user_details: dict[str, Any]
