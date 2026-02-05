from fastapi import APIRouter, HTTPException

from argolocks.models import (
    CreateLockRequest,
    CreateLockResponse,
    Lock,
    LockStatusResponse,
)
from argolocks.slack_client import is_prod_app, send_approval_message
from argolocks.store import create_lock, get_lock

router = APIRouter(prefix="/api/v1/locks", tags=["locks"])


@router.post("", response_model=CreateLockResponse)
def create(req: CreateLockRequest):
    if not is_prod_app(req.app_name):
        raise HTTPException(400, "Only prod apps require approval locks")
    lock = Lock(app_name=req.app_name, triggered_by=req.triggered_by)
    create_lock(lock)
    ts = send_approval_message(lock)
    lock.slack_message_ts = ts
    return CreateLockResponse(
        lock_id=lock.lock_id, status=lock.status, app_name=lock.app_name
    )


@router.get("/{lock_id}", response_model=LockStatusResponse)
def status(lock_id: str):
    lock = get_lock(lock_id)
    if not lock:
        raise HTTPException(404, "Lock not found")
    return LockStatusResponse(
        lock_id=lock.lock_id,
        status=lock.status,
        app_name=lock.app_name,
        decided_by=lock.decided_by,
    )
