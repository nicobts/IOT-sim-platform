"""
SIM card and related schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== SIM Schemas ====================

class SIMBase(BaseModel):
    """Base SIM schema"""

    iccid: str = Field(..., min_length=19, max_length=20)
    imsi: Optional[str] = Field(None, min_length=14, max_length=15)
    msisdn: Optional[str] = None
    label: Optional[str] = None


class SIMCreate(SIMBase):
    """Schema for creating a SIM record"""

    organization_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class SIMUpdate(BaseModel):
    """Schema for updating SIM information"""

    label: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SIMResponse(SIMBase):
    """Schema for SIM response"""

    id: int
    status: Optional[str] = None
    ip_address: Optional[str] = None
    imei: Optional[str] = None
    organization_id: Optional[int] = None
    last_synced_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Usage Schemas ====================

class UsageBase(BaseModel):
    """Base usage schema"""

    timestamp: datetime
    volume_rx: int = Field(0, ge=0)
    volume_tx: int = Field(0, ge=0)
    total_volume: int = Field(0, ge=0)
    sms_mo: int = Field(0, ge=0)
    sms_mt: int = Field(0, ge=0)


class UsageCreate(UsageBase):
    """Schema for creating usage record"""

    iccid: str


class UsageResponse(UsageBase):
    """Schema for usage response"""

    id: int
    iccid: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Connectivity Schemas ====================

class ConnectivityBase(BaseModel):
    """Base connectivity schema"""

    timestamp: datetime
    connected: Optional[bool] = None
    cell_id: Optional[str] = None
    signal_strength: Optional[int] = None
    rat: Optional[str] = None
    country_code: Optional[str] = None
    operator_name: Optional[str] = None


class ConnectivityResponse(ConnectivityBase):
    """Schema for connectivity response"""

    id: int
    iccid: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Event Schemas ====================

class EventBase(BaseModel):
    """Base event schema"""

    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    timestamp: datetime


class EventResponse(EventBase):
    """Schema for event response"""

    id: int
    iccid: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Quota Schemas ====================

class QuotaBase(BaseModel):
    """Base quota schema"""

    quota_type: str = Field(..., pattern="^(data|sms)$")
    volume: Optional[int] = None
    threshold_percentage: Optional[int] = Field(None, ge=0, le=100)
    auto_reload: bool = False


class QuotaResponse(QuotaBase):
    """Schema for quota response"""

    id: int
    iccid: str
    last_volume_added: Optional[int] = None
    last_status_change_date: Optional[datetime] = None
    status: Optional[str] = None
    threshold_volume: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopUpRequest(BaseModel):
    """Schema for quota top-up request"""

    quota_type: str = Field(..., pattern="^(data|sms)$")
    volume: int = Field(..., gt=0)


# ==================== SMS Schemas ====================

class SMSBase(BaseModel):
    """Base SMS schema"""

    message: str = Field(..., min_length=1, max_length=160)


class SMSSendRequest(SMSBase):
    """Schema for sending SMS"""

    destination_address: Optional[str] = None


class SMSResponse(SMSBase):
    """Schema for SMS response"""

    id: int
    iccid: str
    direction: str
    source_address: Optional[str] = None
    destination_address: Optional[str] = None
    status: Optional[str] = None
    submit_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Pagination ====================

class PaginatedResponse(BaseModel):
    """Generic paginated response"""

    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class SIMListResponse(BaseModel):
    """Paginated SIM list response"""

    items: List[SIMResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
