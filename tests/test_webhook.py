import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pingpal.agent as agent_module
from pingpal.api.webhook import handle_challenge, handle_webhook, store


def make_sig(payload: bytes) -> str:
    return "sha256=" + hmac.new(
        b"dev-app-secret",
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()


def make_payload(*, sender: str = "u1", thread: str = "t1", mid: str = "m1", text: str = "hi") -> dict:
    """Build a minimal real Messenger webhook payload."""
    return {
        "object": "page",
        "entry": [
            {
                "id": thread,
                "messaging": [
                    {
                        "sender": {"id": sender},
                        "recipient": {"id": thread},
                        "timestamp": 1234567890,
                        "message": {"mid": mid, "text": text},
                    }
                ],
            }
        ],
    }


def _mock_claude(reply: str = "pong") -> MagicMock:
    client = MagicMock()
    client.messages.create.return_value = MagicMock(content=[MagicMock(text=reply)])
    return client


def test_webhook_challenge_success() -> None:
    res = handle_challenge(
        {
            "hub.mode": "subscribe",
            "hub.verify_token": "dev-verify-token",
            "hub.challenge": "abc123",
        }
    )
    assert res.status_code == 200
    assert res.body == "abc123"


def test_webhook_requires_valid_signature() -> None:
    payload = make_payload()
    body = json.dumps(payload).encode("utf-8")
    res = handle_webhook(payload=payload, raw_body=body, signature_header=None)
    assert res.status_code == 401


def test_webhook_rejects_non_page_object() -> None:
    payload = {"object": "user", "entry": []}
    body = json.dumps(payload).encode("utf-8")
    res = handle_webhook(payload=payload, raw_body=body, signature_header=make_sig(body))
    assert res.status_code == 400


def test_webhook_processes_message_and_replies() -> None:
    store.processed_events.clear()
    store.messages.clear()

    payload = make_payload(sender="u1", thread="t1", mid="m1", text="hello")
    body = json.dumps(payload).encode("utf-8")

    with patch.object(agent_module, "_client", _mock_claude("hey!")):
        res = handle_webhook(payload=payload, raw_body=body, signature_header=make_sig(body))

    assert res.status_code == 200
    assert res.replies == [("u1", "hey!")]
    assert len(store.messages) == 2  # user + bot


def test_webhook_idempotency() -> None:
    store.processed_events.clear()
    store.messages.clear()

    payload = make_payload(sender="u1", thread="t1", mid="m2", text="ping")
    body = json.dumps(payload).encode("utf-8")
    sig = make_sig(body)

    with patch.object(agent_module, "_client", _mock_claude("pong")):
        first = handle_webhook(payload=payload, raw_body=body, signature_header=sig)
        second = handle_webhook(payload=payload, raw_body=body, signature_header=sig)

    assert first.replies == [("u1", "pong")]
    assert second.replies == []  # duplicate, skipped
    assert len(store.messages) == 2  # only one round stored


def test_webhook_skips_non_text_events() -> None:
    store.processed_events.clear()
    store.messages.clear()

    payload = {
        "object": "page",
        "entry": [{"messaging": [{"sender": {"id": "u1"}, "recipient": {"id": "t1"}, "message": {"mid": "m3"}}]}],
    }
    body = json.dumps(payload).encode("utf-8")
    res = handle_webhook(payload=payload, raw_body=body, signature_header=make_sig(body))

    assert res.status_code == 200
    assert res.replies == []
    assert len(store.messages) == 0


def test_webhook_multiple_events_in_one_call() -> None:
    store.processed_events.clear()
    store.messages.clear()

    payload = {
        "object": "page",
        "entry": [
            {
                "messaging": [
                    {"sender": {"id": "u1"}, "recipient": {"id": "t1"}, "message": {"mid": "m4", "text": "first"}},
                    {"sender": {"id": "u2"}, "recipient": {"id": "t1"}, "message": {"mid": "m5", "text": "second"}},
                ]
            }
        ],
    }
    body = json.dumps(payload).encode("utf-8")

    with patch.object(agent_module, "_client", _mock_claude("ok")):
        res = handle_webhook(payload=payload, raw_body=body, signature_header=make_sig(body))

    assert res.status_code == 200
    assert len(res.replies) == 2
    assert res.replies[0][0] == "u1"
    assert res.replies[1][0] == "u2"
