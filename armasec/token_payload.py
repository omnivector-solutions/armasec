"""
This module defines a pydantic schema for the payload of a jwt.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel


class TokenPayload(BaseModel):
    """
    A convenience class that can be used to access parts of a decoded jwt.
    """

    sub: str
    permissions: List[str]
    expire: datetime

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

    @classmethod
    def from_dict(cls, payload_dict: dict) -> TokenPayload:
        """
        Constructs a TokenPayload from a dictionary produced by `jwt.decode()`.
        """
        return cls(
            sub=payload_dict["sub"],
            permissions=payload_dict.get("permissions", list()),
            expire=datetime.fromtimestamp(payload_dict["exp"], tz=timezone.utc),
        )
