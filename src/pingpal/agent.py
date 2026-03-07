import anthropic

from pingpal.db.store import MessageRecord

SYSTEM_PROMPT = (
    "You are PingPal, a friendly and concise assistant in a Messenger group chat. "
    "Keep replies short and helpful."
)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def generate_reply(current_text: str, history: list[MessageRecord]) -> str:
    system = SYSTEM_PROMPT
    if history:
        lines = "\n".join(
            f"{'PingPal' if m.role == 'assistant' else m.user_id}: {m.text}"
            for m in history[-20:]
        )
        system = f"{SYSTEM_PROMPT}\n\nRecent conversation:\n{lines}"

    response = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=system,
        messages=[{"role": "user", "content": current_text}],
    )
    return response.content[0].text
