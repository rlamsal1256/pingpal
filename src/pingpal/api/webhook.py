from dataclasses import dataclass

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
    reply_to: str | None = None
    reply_text: str | None = None


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


def handle_event(*, payload: dict, raw_body: bytes, signature_header: str | None) -> WebhookResult:
    try:
        verify_signature(signature_header, raw_body, settings.messenger_app_secret)
    except MessengerVerificationError as exc:
        return WebhookResult(status_code=401, body={"detail": str(exc)})

    event_id = payload.get("id")
    if not event_id:
        return WebhookResult(status_code=400, body={"detail": "Missing event id"})

    if not store.mark_event_processed(event_id):
        return WebhookResult(status_code=200, body={"status": "duplicate", "event_id": event_id})

    message = payload.get("message", {})
    message_id = message.get("mid", event_id)
    text = message.get("text", "")
    sender_id = payload.get("sender", {}).get("id", "unknown")
    thread_id = payload.get("recipient", {}).get("id", "group")

    history = store.get_thread_messages(thread_id)
    store.add_message(message_id=message_id, thread_id=thread_id, user_id=sender_id, text=text)
    reply = generate_reply(current_text=text, history=history)
    store.add_message(
        message_id=f"bot-{message_id}",
        thread_id=thread_id,
        user_id="pingpal",
        text=reply,
        role="assistant",
    )
    return WebhookResult(
        status_code=200,
        body={"status": "processed", "event_id": event_id},
        reply_to=sender_id,
        reply_text=reply,
    )
