import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

from pingpal.api.webhook import handle_challenge, handle_event, store


def make_sig(payload: bytes) -> str:
    return "sha256=" + hmac.new(
        b"dev-app-secret",
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()


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
    payload = {"id": "evt-1", "sender": {"id": "u1"}, "recipient": {"id": "t1"}, "message": {"mid": "m1", "text": "hi"}}
    body = json.dumps(payload).encode("utf-8")
    res = handle_event(payload=payload, raw_body=body, signature_header=None)
    assert res.status_code == 401


def test_webhook_idempotency() -> None:
    store.processed_events.clear()
    store.messages.clear()

    payload = {"id": "evt-2", "sender": {"id": "u1"}, "recipient": {"id": "t1"}, "message": {"mid": "m2", "text": "ping"}}
    body = json.dumps(payload).encode("utf-8")
    signature = make_sig(body)

    import pingpal.agent as agent_module
    with patch.object(agent_module, "_client", _mock_claude("pong")):
        first = handle_event(payload=payload, raw_body=body, signature_header=signature)
        second = handle_event(payload=payload, raw_body=body, signature_header=signature)

    assert first.status_code == 200
    assert first.body["status"] == "processed"
    assert first.reply_to == "u1"
    assert first.reply_text == "pong"
    assert second.status_code == 200
    assert second.body["status"] == "duplicate"
    assert second.reply_to is None
    assert len(store.messages) == 2  # user message + bot reply
