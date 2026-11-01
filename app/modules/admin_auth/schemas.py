from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AdminProfile(BaseModel):
    email: str
    full_name: str | None
    firebase_uid: str
    last_login_at: datetime | None
