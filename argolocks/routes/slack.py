import json

from fastapi import APIRouter, Form, HTTPException

from argolocks.models import LockStatus
from argolocks.slack_client import update_message_with_decision
from argolocks.store import get_lock

router = APIRouter(prefix="/api/v1/slack", tags=["slack"])


@router.post("/actions")
def handle_action(payload: str = Form(...)):
    data = json.loads(payload)
    actions = data.get("actions", [])
    if not actions:
        raise HTTPException(400, "No actions in payload")
    action = actions[0]
    lock_id = action["value"]
    lock = get_lock(lock_id)
    if not lock:
        raise HTTPException(404, "Lock not found")
    if lock.status != LockStatus.PENDING:
        return {"ok": True, "message": "Already decided"}
    user = data.get("user", {}).get("username", "unknown")
    if action["action_id"] == "approve_lock":
        lock.status = LockStatus.APPROVED
    elif action["action_id"] == "deny_lock":
        lock.status = LockStatus.DENIED
    else:
        raise HTTPException(400, "Unknown action")
    lock.decided_by = user
    update_message_with_decision(lock)
    return {"ok": True}
