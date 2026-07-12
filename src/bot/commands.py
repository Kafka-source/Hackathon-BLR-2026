import re
from microsoft_agents.hosting.core import TurnContext

COMMAND_PATTERNS = {
    "update_ticket": re.compile(r"^/update-ticket\s*$", re.IGNORECASE),
    "reassign": re.compile(r"^/reassign\s+(.+)$", re.IGNORECASE),
    "add_note": re.compile(r"^/add-note\s+(.+)$", re.IGNORECASE),
}


async def get_chat_title(context: TurnContext) -> str:
    channel_data = context.activity.channel_data or {}
    channel_name = channel_data.get("channel", {}).get("name")
    return channel_name or getattr(context.activity.conversation, "name", "") or ""


async def get_sender_upn(context: TurnContext) -> str:
    return getattr(context.activity.from_property, "aad_object_id", "") or \
        getattr(context.activity.from_property, "name", "")


async def handle_command(name: str, match, context: TurnContext, ticket_meta: dict, conversation_id: str, snow_client, ticket_ctx, convo_store):
    inc_number = ticket_meta["inc_number"]

    if name == "reassign":
        target_group = match.group(1).strip()
        ok = await snow_client.reassign_ticket(inc_number, target_group)
        if ok:
            ticket_ctx.invalidate(conversation_id)
            await context.send_activity(f"{inc_number} reassigned to {target_group}.")
        else:
            await context.send_activity("Reassignment failed.")

    elif name == "add_note":
        note = match.group(1).strip()
        ok = await snow_client.add_comment(inc_number, note)
        await context.send_activity("Note added." if ok else "Failed to add note.")
