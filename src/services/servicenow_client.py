import asyncio

class ServiceNowClient:

    def __init__(self):
        self._tickets = {}

    async def get_ticket(self, inc_number: str) -> dict:
        ...
    
    async def create_ticket(self, desc: str) -> dict:
        ...

    async def add_work_note(self, inc_number: str, note: str) -> bool:
        ...

    async def reassign_ticket(self, inc_number: str, target_group: str) -> bool:
        ...

    async def add_comment(self, inc_number: str, note: str) -> bool:
        ...

snow = ServiceNowClient()