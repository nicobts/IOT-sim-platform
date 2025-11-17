"""
Authentication and authorization schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class TokenData(BaseModel):
    """Token payload data"""

    sub: str
    exp: Optional[datetime] = None
    type: str = "access"


class Login(BaseModel):
    """Login request schema"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class RefreshToken(BaseModel):
    """Refresh token request schema"""

    refresh_token: str


class APIKeyCreate(BaseModel):
    """API key creation request"""

    name: Optional[str] = Field(None, max_length=100)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key response (only returned once on creation)"""

    api_key: str
    id: int
    name: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyInfo(BaseModel):
    """API key information (without the actual key)"""

    id: int
    name: Optional[str] = None
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
