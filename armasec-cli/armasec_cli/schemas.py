from typing import Optional

import httpx
from pydantic import BaseModel

from armasec_cli.config import Settings


class TokenSet(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


class IdentityData(BaseModel):
    client_id: str
    email: Optional[str] = None


class Persona(BaseModel):
    token_set: TokenSet
    identity_data: IdentityData


class DeviceCodeData(BaseModel):
    device_code: str
    verification_uri_complete: str
    interval: int


class CliContext(BaseModel, arbitrary_types_allowed=True):
    persona: Optional[Persona] = None
    client: Optional[httpx.Client] = None
    settings: Optional[Settings] = None
