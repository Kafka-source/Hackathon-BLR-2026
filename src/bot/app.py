import re
import logging
from pathlib import Path

from microsoft_agents.hosting.core import TurnContext, TurnState

from services.servicenow_client import ServiceNowClient
from core.ticket_context import TicketContext
from core.conversation_store import ConversationStore
from bot.commands import COMMAND_PATTERNS, handle_command, get_chat_title, get_sender_upn
from bot.agent import PixelAgentClient

snow_client = ServiceNowClient()
ticket_ctx = TicketContext(snow_client)
convo_store = ConversationStore()
agent_client = PixelAgentClient()

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "pixel_bot.log"

logger = logging.getLogger("pixel_bot")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.propagate = False


async def _resolve_chat_title(context: TurnContext) -> str:
    """Resolves the Teams chat/group/team title, falling back to channel_data.team.name
    if get_chat_title() (conversation.name) comes back empty."""
    chat_title = await get_chat_title(context)
    if not chat_title and getattr(context.activity, "channel_data", None):
        chat_title = context.activity.channel_data.get(
            "team", {}).get("name", "")
    return chat_title


def _clean_message_text(context: TurnContext) -> str:
    text = context.activity.text or ""
    text = re.sub(r"<at>.*?</at>", "", text, flags=re.IGNORECASE)
    if context.activity.recipient and context.activity.recipient.name:
        text = text.replace(f"@{context.activity.recipient.name}", "")
    text = text.replace("@Pixel", "").replace("@pixel", "")
    return text.strip()


def register_handlers(agent_app):
    @agent_app.conversation_update("membersAdded")
    async def on_members_added(context: TurnContext, state: TurnState):
        for member in context.activity.members_added:
            if member.id != context.activity.recipient.id:
                await context.send_activity(
                    "Pixel is online for this ticket. Agents can use /update-ticket, /reassign, /add-note."
                )

    @agent_app.activity("message")
    async def on_message(context: TurnContext, state: TurnState):
        text = _clean_message_text(context)
        if not text:
            return

        conversation_id = context.activity.conversation.id
        sender_name = getattr(context.activity.from_property, "name", "User")
        sender_upn = await get_sender_upn(context)

        logger.info(
            f"[conv={conversation_id}] sender_name={sender_name!r} sender_upn={sender_upn!r}")

        chat_title = await _resolve_chat_title(context)
        if not chat_title:
            logger.warning(
                f"[conv={conversation_id}] chat_title resolved empty; "
                f"conversation={vars(context.activity.conversation) if context.activity.conversation else 'None'}, "
                f"channel_data={context.activity.channel_data}"
            )

        ticket_meta = await ticket_ctx.get_ticket_meta(conversation_id, chat_title)

        if not ticket_meta:
            inc_match = re.search(r"(INC\d+)", text, re.IGNORECASE)
            if inc_match:
                inc_fallback = inc_match.group(1).upper()
                ticket_meta = await ticket_ctx.get_ticket_meta(conversation_id, inc_fallback)

        is_agent = ticket_ctx.is_agent(
            ticket_meta, sender_upn) if ticket_meta else False

        for name, pattern in COMMAND_PATTERNS.items():
            match = pattern.match(text)
            if match:
                if not ticket_meta:
                    await context.send_activity("Couldn't resolve a ticket from this chat's title.")
                    return
                if not is_agent:
                    await context.send_activity("Only the assigned agent can use bot commands.")
                    return
                await handle_command(
                    name, match, context, ticket_meta, conversation_id, snow_client, ticket_ctx, convo_store
                )
                return

        convo_store.append(conversation_id, sender_name, text)

        title_str = chat_title or "No Title"
        prompt_text = f"{sender_name}: {text}"

        if not agent_client.get_context(conversation_id):
            if ticket_meta:
                inc_number = ticket_meta.get("inc_number", "")
                desc = ticket_meta.get("short_description", "")
                prompt_text = (
                    f"[System Context: The Teams group chat title is '{title_str}'. "
                    f"Known Ticket {inc_number} is active for issue: {desc}.]\n\n{sender_name}: {text}"
                )
            else:
                prompt_text = (
                    f"[System Context: The Teams group chat title is '{title_str}'.]\n\n{sender_name}: {text}"
                )

        logger.info(f"[conv={conversation_id}] Sending to AI: {prompt_text}")

        final_text = await agent_client.send_message(
            prompt_text=prompt_text,
            conversation_id=conversation_id,
            sender_name=sender_name,
            sender_upn=sender_upn,
            chat_title=chat_title,
            is_agent=is_agent,
            ticket_meta=ticket_meta,
        )

        if final_text:
            await context.send_activity(final_text)
            convo_store.append(conversation_id, "Pixel", final_text)
