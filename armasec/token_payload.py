"""
This module defines a pydantic schema for the payload of a jwt.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict, BaseModel, Field, AliasChoices


class TokenPayload(BaseModel):
    """
    A convenience class that can be used to access parts of a decoded jwt.

    Attributes:
        sub:            The "sub" claim from a JWT.
        permissions:    The permissions claims extracted from a JWT.
        expire:         The "exp" claim extracted from a JWT.
        client_id:      The "azp" claim extracted from a JWT.
        original_token: The original token value
    """

    sub: str
    permissions: List[str] = Field(list())
    expire: Optional[datetime] = Field(None, validation_alias=AliasChoices("exp", "expire"))
    client_id: Optional[str] = Field(None, validation_alias=AliasChoices("azp", "client_id"))
    original_token: Optional[str] = None
    model_config = ConfigDict(extra="allow")

    def to_dict(self):
        """
        Convert a TokenPayload to the equivalent dictionary returned by `jwt.decode()`.
        """
        return dict(
            sub=self.sub,
            permissions=self.permissions,
            exp=int(self.expire.timestamp()),
            client_id=self.client_id,
        )
