from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class MessageRecord:
    message_id: str
    thread_id: str
    user_id: str
    text: str
    role: str
    created_at: datetime


class InMemoryStore:
    def __init__(self) -> None:
        self.processed_events: set[str] = set()
        self.messages: list[MessageRecord] = []

    def mark_event_processed(self, event_id: str) -> bool:
        """Returns True if this event is newly processed, False if duplicate."""
        if event_id in self.processed_events:
            return False
        self.processed_events.add(event_id)
        return True

    def add_message(self, *, message_id: str, thread_id: str, user_id: str, text: str, role: str = "user") -> None:
        self.messages.append(
            MessageRecord(
                message_id=message_id,
                thread_id=thread_id,
                user_id=user_id,
                text=text,
                role=role,
                created_at=datetime.now(tz=timezone.utc),
            )
        )
