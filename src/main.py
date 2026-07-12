import os
from aiohttp import web
from dotenv import load_dotenv
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter, jwt_authorization_middleware, start_agent_process
from microsoft_agents.hosting.core import Authorization, AgentApplication, TurnState, MemoryStorage

from bot.app import register_handlers

load_dotenv()

agents_sdk_config = load_configuration_from_env(os.environ)
storage = MemoryStorage()
connection_manager = MsalConnectionManager(**agents_sdk_config)
adapter = CloudAdapter(connection_manager=connection_manager)
authorization = Authorization(storage, connection_manager, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=storage, adapter=adapter, authorization=authorization)
register_handlers(AGENT_APP)

app = web.Application(middlewares=[jwt_authorization_middleware])
app["agent_configuration"] = connection_manager.get_default_connection_configuration()
app["agent_app"] = AGENT_APP
app["adapter"] = adapter


async def messages(req: web.Request) -> web.Response:
    return await start_agent_process(req, req.app["agent_app"], req.app["adapter"])

app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    web.run_app(app, port=int(os.environ.get("PORT", 3978)))
