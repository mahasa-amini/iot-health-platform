from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field


# # ======================================================
# # Core / Shared Schemas
# # ======================================================

class AlertAckRequest(BaseModel):
    """
    Payload used when acknowledging an alert.

    اطلاعاتی که هنگام acknowledge کردن هشدار ارسال می‌شود.
    """
    reviewed_by: Optional[str] = None
    clinical_note: Optional[str] = None


class PatientCreateRequest(BaseModel):
    """
    Payload received from UI to create a new patient.
    """
    name: str = Field(..., min_length=1)
    age: Optional[int] = Field(None, ge=0)
    gender: Optional[str] = Field(None)
    phone: Optional[str] = Field(None)
    threshold_profile: str = Field(...)
    wristband_id: int | None = None


class WristbandCreateRequest(BaseModel):
    wristband_id: int
    # created_at: datetime = Field(default_factory=datetime.utcnow)