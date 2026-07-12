import json
import logging
from typing import Optional

import aiohttp

logger = logging.getLogger("pixel_bot")

DEFAULT_AGENT_URL = "http://localhost:8080/api/v1/pixel_agent/streaming_chat"


class PixelAgentClient:

    def __init__(self, url: str = DEFAULT_AGENT_URL):
        self.url = url
        self._chat_contexts: dict[str, dict] = {}

    def get_context(self, conversation_id: str) -> dict:
        """Returns the stored chat_context for a conversation, or {} if none yet."""
        return self._chat_contexts.get(conversation_id, {})

    def _build_payload(
        self,
        *,
        prompt_text: str,
        conversation_id: str,
        sender_name: str,
        sender_upn: Optional[str],
        chat_title: str,
        is_agent: bool,
        ticket_meta: Optional[dict],
    ) -> dict:
        return {
            "user_message": {"text": prompt_text},
            "chat_context": self.get_context(conversation_id),
            "metadata": {
                "source": "teams_bot",
                "conversation_id": conversation_id,
                "sender_name": sender_name,
                "sender_upn": sender_upn,
                "chat_title": chat_title,
                "is_agent": is_agent,
                "ticket": {
                    "inc_number": ticket_meta.get("inc_number") if ticket_meta else None,
                    "short_description": ticket_meta.get("short_description") if ticket_meta else None,
                } if ticket_meta else None,
            },
        }

    async def send_message(
        self,
        *,
        prompt_text: str,
        conversation_id: str,
        sender_name: str,
        sender_upn: Optional[str],
        chat_title: str,
        is_agent: bool,
        ticket_meta: Optional[dict],
    ) -> Optional[str]:
        payload = self._build_payload(
            prompt_text=prompt_text,
            conversation_id=conversation_id,
            sender_name=sender_name,
            sender_upn=sender_upn,
            chat_title=chat_title,
            is_agent=is_agent,
            ticket_meta=ticket_meta,
        )
        logger.debug(
            f"[conv={conversation_id}] outgoing payload: {json.dumps(payload, default=str)}")

        final_text: Optional[str] = None
        new_chat_context = None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=payload) as response:
                    if response.status != 200:
                        logger.error(
                            f"[conv={conversation_id}] Neuro-San returned status {response.status}")
                        return None

                    async for line in response.content:
                        if not line:
                            continue
                        try:
                            msg = json.loads(line.decode("utf-8"))
                        except json.JSONDecodeError:
                            logger.warning(
                                f"[conv={conversation_id}] failed to decode stream line: {line!r}")
                            continue

                        logger.debug(
                            f"[conv={conversation_id}] stream chunk: {msg}")
                        resp = msg.get("response", {})

                        if resp.get("text"):
                            final_text = resp["text"]

                        if "chat_context" in resp:
                            new_chat_context = resp["chat_context"]
                        elif "chat_context" in msg:
                            new_chat_context = msg["chat_context"]
        except Exception as e:
            logger.exception(
                f"[conv={conversation_id}] Unexpected error calling Neuro-San: {e}")
            return None

        if new_chat_context is not None:
            self._chat_contexts[conversation_id] = new_chat_context
            logger.info(
                f"[conv={conversation_id}] updated chat_context: {new_chat_context}")
        else:
            logger.warning(
                f"[conv={conversation_id}] no chat_context found in any stream chunk")

        if not final_text:
            logger.warning(
                f"[conv={conversation_id}] no final_text extracted from stream")

        return final_text
