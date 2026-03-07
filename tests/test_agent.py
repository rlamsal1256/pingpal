from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pingpal.agent as agent_module
from pingpal.agent import generate_reply
from pingpal.db.store import MessageRecord


def make_record(user_id: str, text: str, role: str = "user") -> MessageRecord:
    return MessageRecord(
        message_id="m",
        thread_id="t",
        user_id=user_id,
        text=text,
        role=role,
        created_at=datetime.now(tz=timezone.utc),
    )


def mock_client(reply: str) -> MagicMock:
    client = MagicMock()
    client.messages.create.return_value = MagicMock(content=[MagicMock(text=reply)])
    return client


def test_generate_reply_no_history() -> None:
    client = mock_client("hello!")
    with patch.object(agent_module, "_client", client):
        result = generate_reply("hi", history=[])

    assert result == "hello!"
    client.messages.create.assert_called_once()
    call_kwargs = client.messages.create.call_args.kwargs
    assert call_kwargs["messages"] == [{"role": "user", "content": "hi"}]
    assert "Recent conversation" not in call_kwargs["system"]


def test_generate_reply_includes_history_in_system() -> None:
    history = [
        make_record("alice", "hey"),
        make_record("pingpal", "hey alice!", role="assistant"),
    ]
    client = mock_client("sure")
    with patch.object(agent_module, "_client", client):
        generate_reply("can you help?", history=history)

    call_kwargs = client.messages.create.call_args.kwargs
    assert "alice: hey" in call_kwargs["system"]
    assert "PingPal: hey alice!" in call_kwargs["system"]
