"""API routes for agents."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from mission_control.agents import agent_manager

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentCreate(BaseModel):
    id: str
    name: str
    personality: Optional[str] = ""


class MessageSend(BaseModel):
    message: str


@router.get("/")
async def list_agents():
    """Get all registered agents."""
    agents = await agent_manager.get_all_agents()
    return {"agents": agents}


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get a specific agent."""
    agent = await agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/")
async def create_agent(agent: AgentCreate):
    """Register a new agent."""
    await agent_manager.register_agent(agent.id, agent.name, agent.personality)
    return {"status": "created", "agent_id": agent.id}


@router.post("/{agent_id}/message")
async def send_message(agent_id: str, body: MessageSend):
    """Send a message to an agent."""
    response = await agent_manager.send_message_to_agent(agent_id, body.message)
    return {"response": response}


@router.patch("/{agent_id}/status")
async def update_agent_status(agent_id: str, status: str):
    """Update an agent's status."""
    await agent_manager.update_status(agent_id, status)
    return {"status": "updated"}
