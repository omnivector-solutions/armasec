"""
This module defines a pydantic schema for the payload of a jwt.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field, validator


class TokenPayload(BaseModel):
    """
    A convenience class that can be used to access parts of a decoded jwt.
    """

    sub: str
    permissions: List[str] = None
    expire: datetime = Field(None, alias='exp')

    class Config:
        extra = "allow"

    @validator('permissions', pre=True, always=True)
    def validate_permissions(cls, v):
        return v or list()

    def to_dict(self):
        """
        Converts a TokenPayload to the equivalent dictionary returned by `jwt.decode()`.
        """
        return dict(
            sub=self.sub,
            permissions=self.permissions,
            exp=int(self.expire.timestamp()),
        )
