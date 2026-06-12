"""Mission Control AI — Main server entry point."""

import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from mission_control.database import init_db
from mission_control.api.agents import router as agents_router
from mission_control.api.tasks import router as tasks_router
from mission_control.api.messages import router as messages_router
from mission_control.api.settings import router as settings_router
from mission_control.api.files import router as files_router
from mission_control.api.websocket import ws_manager
from mission_control.agents import agent_manager
from mission_control.agents.idle_chat import idle_scheduler

# Server port — change this if needed
PORT = 8600


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("🚀 Mission Control AI starting up...")
    await init_db()
    print("✅ Database initialized")

    # Register default agents if none exist, or update names if they do
    agents = await agent_manager.get_all_agents()
    if not agents:
        print("📝 No agents found. Registering agents...")
        await agent_manager.register_agent("agent-1", "Rin", "Onee-san. Delegator. Affectionate, lightly yandere.")
        await agent_manager.register_agent("agent-2", "Mei", "Diligent, precise, reliable. Formal-leaning.")
        await agent_manager.register_agent("agent-3", "Yui", "Cheerful, curious, talkative. The energy of the group.")
        print("✅ Rin, Mei, and Yui registered")
    else:
        # Ensure names are up to date
        from mission_control.database import get_db
        db = await get_db()
        try:
            await db.execute("UPDATE agents SET name = 'Rin', personality = 'Onee-san. Delegator.' WHERE id = 'agent-1'")
            await db.execute("UPDATE agents SET name = 'Mei', personality = 'Diligent, precise, reliable.' WHERE id = 'agent-2'")
            await db.execute("UPDATE agents SET name = 'Yui', personality = 'Cheerful, curious, talkative.' WHERE id = 'agent-3'")
            await db.commit()
        finally:
            await db.close()
        print("✅ Agent names updated (Rin, Mei, Yui)")

    # Start idle chat scheduler
    await idle_scheduler.start()
    print("✅ Idle chat scheduler started")

    print("🟢 Mission Control AI is running!")
    print(f"   Dashboard: http://localhost:{PORT}")
    print(f"   API docs:  http://localhost:{PORT}/docs")

    yield

    # Shutdown
    await idle_scheduler.stop()
    print("🔴 Mission Control AI shutting down...")


# Create app
app = FastAPI(
    title="Mission Control AI",
    description="A virtual office for AI agents",
    version="0.1.0",
    lifespan=lifespan
)

# CORS (allow local frontend dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(agents_router)
app.include_router(tasks_router)
app.include_router(messages_router)
app.include_router(settings_router)
app.include_router(files_router)


# Health check
@app.get("/api/health")
async def health_check():
    """Basic health check."""
    agents = await agent_manager.get_all_agents()
    return {
        "status": "ok",
        "agents_count": len(agents),
        "version": "0.1.0"
    }


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time chat and status updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Receive messages from client (e.g., user sending a chat)
            data = await websocket.receive_json()

            if data.get("type") == "dm":
                # User sends a DM to an agent
                agent_id = data.get("agent_id")
                message = data.get("message", "")
                response = await agent_manager.send_message_to_agent(agent_id, message)

                # Send response back via WebSocket
                await ws_manager.send_personal(websocket, {
                    "type": "dm_response",
                    "agent_id": agent_id,
                    "message": message,
                    "response": response
                })

            elif data.get("type") == "group":
                # User sends a message to group chat
                import random
                message = data.get("message", "")

                # Store user message
                from mission_control.database import get_db
                db = await get_db()
                try:
                    await db.execute(
                        "INSERT INTO messages (from_agent, to_agent, chat_type, content) VALUES (?, ?, ?, ?)",
                        ("user", "group", "group", message)
                    )
                    await db.commit()
                finally:
                    await db.close()

                # Pick a random agent to respond
                agents_list = await agent_manager.get_all_agents()
                if agents_list:
                    responder = random.choice(agents_list)
                    from mission_control.agents.manager import AGENT_PROFILES
                    profile = AGENT_PROFILES.get(responder["id"], "rin")
                    
                    # Generate response
                    group_prompt = f"Faris-kun just said in the group chat: \"{message}\". Respond naturally and briefly (1-3 sentences)."
                    response = await agent_manager._call_hermes(profile, group_prompt, persist=False)

                    # Store agent response
                    db = await get_db()
                    try:
                        await db.execute(
                            "INSERT INTO messages (from_agent, to_agent, chat_type, content) VALUES (?, ?, ?, ?)",
                            (responder["id"], "group", "group", response)
                        )
                        await db.commit()
                    finally:
                        await db.close()

                    # Broadcast to all clients
                    await ws_manager.broadcast({
                        "type": "group_chat",
                        "messages": [{
                            "from_agent": responder["id"],
                            "from_name": responder["name"],
                            "content": response,
                            "timestamp": __import__('datetime').datetime.now().isoformat(),
                            "chat_type": "group"
                        }]
                    })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# Serve static files (frontend) — will add later
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


def main():
    """Run the server."""
    uvicorn.run(
        "mission_control.main:app",
        host="127.0.0.1",
        port=PORT,
        reload=False
    )


if __name__ == "__main__":
    main()
