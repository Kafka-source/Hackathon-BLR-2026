from datetime import datetime, timezone

class ConversationStore:
    def __init__(self):
        self._store: dict[str, list[dict]] = {}

    def append(self, conversation_id: str, sender: str, text: str):
        self._store.setdefault(conversation_id, []).append({
            "sender": sender,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_transcript(self, conversation_id: str) -> list[dict]:
        return self._store.get(conversation_id, [])

    def clear(self, conversation_id: str):
        self._store.pop(conversation_id, None)