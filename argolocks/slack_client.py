import re

from slack_sdk import WebClient

from argolocks.config import settings
from argolocks.models import Lock, LockStatus


def _get_client() -> WebClient:
    return WebClient(token=settings.slack_bot_token)


def is_prod_app(app_name: str) -> bool:
    return bool(re.search(r"prod(uction)?", app_name, re.IGNORECASE))


def send_approval_message(lock: Lock) -> str | None:
    client = _get_client()
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":rocket: *Deployment approval requested*\n*App:* `{lock.app_name}`\n*Triggered by:* {lock.triggered_by}\n*Lock ID:* `{lock.lock_id}`",
            },
        },
        {
            "type": "actions",
            "block_id": f"lock_{lock.lock_id}",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "style": "primary",
                    "action_id": "approve_lock",
                    "value": lock.lock_id,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Deny"},
                    "style": "danger",
                    "action_id": "deny_lock",
                    "value": lock.lock_id,
                },
            ],
        },
    ]
    resp = client.chat_postMessage(
        channel=settings.slack_channel_id,
        text=f"Deployment approval requested for {lock.app_name}",
        blocks=blocks,
    )
    return resp.get("ts")


def update_message_with_decision(lock: Lock) -> None:
    client = _get_client()
    if lock.status == LockStatus.APPROVED:
        emoji = ":white_check_mark:"
        verb = "Approved"
    else:
        emoji = ":x:"
        verb = "Denied"
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{emoji} *Deployment {verb.lower()}*\n*App:* `{lock.app_name}`\n*{verb} by:* {lock.decided_by}",
            },
        },
    ]
    client.chat_update(
        channel=settings.slack_channel_id,
        ts=lock.slack_message_ts,
        text=f"Deployment {verb.lower()} for {lock.app_name}",
        blocks=blocks,
    )
