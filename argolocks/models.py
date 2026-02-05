from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel


class LockStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


@dataclass
class Lock:
    app_name: str
    triggered_by: str
    lock_id: str = field(default_factory=lambda: uuid4().hex[:12])
    status: LockStatus = LockStatus.PENDING
    decided_by: str | None = None
    slack_message_ts: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CreateLockRequest(BaseModel):
    app_name: str
    triggered_by: str = "argocd"


class CreateLockResponse(BaseModel):
    lock_id: str
    status: LockStatus
    app_name: str


class LockStatusResponse(BaseModel):
    lock_id: str
    status: LockStatus
    app_name: str
    decided_by: str | None = None
