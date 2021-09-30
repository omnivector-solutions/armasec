"""
This module defines a pydantic schema for the payload of a jwt.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    """
    A convenience class that can be used to access parts of a decoded jwt.
    """

    sub: str
    permissions: List[str] = Field(list())
    expire: datetime = Field(None, alias="exp")

    class Config:
        extra = "allow"

    def to_dict(self):
        """
        Converts a TokenPayload to the equivalent dictionary returned by `jwt.decode()`.
        """
        return dict(
            sub=self.sub,
            permissions=self.permissions,
            exp=int(self.expire.timestamp()),
        )
