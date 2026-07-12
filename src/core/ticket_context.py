import re
from services.servicenow_client import ServiceNowClient

TITLE_PATTERN = re.compile(r"(INC\d+)", re.IGNORECASE)


class TicketContext:
    def __init__(self, snow_client: ServiceNowClient):
        self.snow = snow_client
        self._cache: dict[str, dict] = {}

    def parse_title(self, chat_title: str) -> str | None:
        match = TITLE_PATTERN.search(chat_title or "")
        return match.group(1).upper() if match else None

    async def get_ticket_meta(self, conversation_id: str, chat_title: str) -> dict | None:
        if conversation_id in self._cache:
            return self._cache[conversation_id]

        inc_number = self.parse_title(chat_title)
        if not inc_number:
            return None

        ticket = await self.snow.get_ticket(inc_number)
        ticket["inc_number"] = inc_number
        self._cache[conversation_id] = ticket
        return ticket

    def is_agent(self, ticket_meta: dict, sender_upn: str) -> bool:
        if not ticket_meta or not sender_upn:
            return False
        return ticket_meta.get("assigned_to_upn", "").lower() == sender_upn.lower()

    def invalidate(self, conversation_id: str):
        self._cache.pop(conversation_id, None)

    async def set_override(self, conversation_id: str, inc_number: str) -> dict:
        ticket = await self.snow.get_ticket(inc_number.upper())
        ticket["inc_number"] = inc_number.upper()
        self._cache[conversation_id] = ticket
        return ticket
