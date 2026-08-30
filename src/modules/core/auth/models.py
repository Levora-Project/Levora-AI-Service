from datetime import datetime

from pydantic import BaseModel


class ApiKeyInfo(BaseModel):

    id: str
    name: str
    is_active: bool
    expires_at: datetime | None = None
