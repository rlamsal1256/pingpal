from dataclasses import dataclass, field

from pingpal.agent import generate_reply
from pingpal.config import settings
from pingpal.db.store import InMemoryStore
from pingpal.services.messenger_verifier import (
    MessengerVerificationError,
    verify_challenge,
    verify_signature,
)


@dataclass(slots=True)
class WebhookResult:
    status_code: int
    body: dict | str
    replies: list[tuple[str, str]] = field(default_factory=list)


store = InMemoryStore()


def handle_challenge(query: dict[str, str | None]) -> WebhookResult:
    try:
        challenge = verify_challenge(
            mode=query.get("hub.mode"),
            token=query.get("hub.verify_token"),
            challenge=query.get("hub.challenge"),
            expected_token=settings.messenger_verify_token,
        )
    except MessengerVerificationError as exc:
        return WebhookResult(status_code=403, body={"detail": str(exc)})
    return WebhookResult(status_code=200, body=challenge)


def handle_webhook(*, payload: dict, raw_body: bytes, signature_header: str | None) -> WebhookResult:
    try:
        verify_signature(signature_header, raw_body, settings.messenger_app_secret)
    except MessengerVerificationError as exc:
        return WebhookResult(status_code=401, body={"detail": str(exc)})

    if payload.get("object") != "page":
        return WebhookResult(status_code=400, body={"detail": "Unsupported object type"})

    replies: list[tuple[str, str]] = []

    for entry in payload.get("entry", []):
        for event in entry.get("messaging", []):
            message = event.get("message", {})
            mid = message.get("mid")
            text = message.get("text", "").strip()

            # skip events without a message id or text (attachments, reactions, etc.)
            if not mid or not text:
                continue

            if not store.mark_event_processed(mid):
                continue

            sender_id = event.get("sender", {}).get("id", "unknown")
            thread_id = event.get("recipient", {}).get("id", "unknown")

            history = store.get_thread_messages(thread_id)
            store.add_message(message_id=mid, thread_id=thread_id, user_id=sender_id, text=text)
            reply = generate_reply(current_text=text, history=history)
            store.add_message(
                message_id=f"bot-{mid}",
                thread_id=thread_id,
                user_id="pingpal",
                text=reply,
                role="assistant",
            )
            replies.append((sender_id, reply))

    return WebhookResult(status_code=200, body={"status": "ok"}, replies=replies)
