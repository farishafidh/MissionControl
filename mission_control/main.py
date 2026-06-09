"""Mission Control AI — Main server entry point."""

import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from mission_control.database import init_db
from mission_control.api.agents import router as agents_router
from mission_control.api.tasks import router as tasks_router
from mission_control.api.messages import router as messages_router
from mission_control.api.settings import router as settings_router
from mission_control.agents import agent_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("🚀 Mission Control AI starting up...")
    await init_db()
    print("✅ Database initialized")

    # Register default agents if none exist
    agents = await agent_manager.get_all_agents()
    if not agents:
        print("📝 No agents found. Registering placeholder agents...")
        await agent_manager.register_agent("agent-1", "Agent 1", "Placeholder personality")
        await agent_manager.register_agent("agent-2", "Agent 2", "Placeholder personality")
        await agent_manager.register_agent("agent-3", "Agent 3", "Placeholder personality")
        print("✅ 3 placeholder agents registered")

    print("🟢 Mission Control AI is running!")
    print("   Dashboard: http://localhost:8500")
    print("   API docs:  http://localhost:8500/docs")

    yield

    # Shutdown
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


# Serve static files (frontend) — will add later
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


def main():
    """Run the server."""
    uvicorn.run(
        "mission_control.main:app",
        host="127.0.0.1",
        port=8500,
        reload=True
    )


if __name__ == "__main__":
    main()
