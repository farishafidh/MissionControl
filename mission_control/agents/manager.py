"""Agent Manager — handles spawning and managing Hermes agent instances."""

import asyncio
import subprocess
import os
from typing import Optional
from dataclasses import dataclass, field

from mission_control.database import get_db


@dataclass
class AgentProcess:
    """Represents a running agent instance."""
    id: str
    name: str
    personality: str
    process: Optional[subprocess.Popen] = None
    status: str = "idle"


class AgentManager:
    """Manages the lifecycle of AI agents."""

    def __init__(self):
        self.agents: dict[str, AgentProcess] = {}

    async def register_agent(self, agent_id: str, name: str, personality: str = ""):
        """Register an agent in the database."""
        db = await get_db()
        try:
            await db.execute(
                "INSERT OR REPLACE INTO agents (id, name, personality, status) VALUES (?, ?, ?, ?)",
                (agent_id, name, personality, "idle")
            )
            await db.commit()
        finally:
            await db.close()

        self.agents[agent_id] = AgentProcess(
            id=agent_id,
            name=name,
            personality=personality
        )

    async def get_all_agents(self) -> list[dict]:
        """Get all registered agents with their status."""
        db = await get_db()
        try:
            cursor = await db.execute("SELECT * FROM agents")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await db.close()

    async def get_agent(self, agent_id: str) -> Optional[dict]:
        """Get a single agent by ID."""
        db = await get_db()
        try:
            cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await db.close()

    async def update_status(self, agent_id: str, status: str):
        """Update an agent's status (idle, working, chatting)."""
        db = await get_db()
        try:
            await db.execute(
                "UPDATE agents SET status = ? WHERE id = ?",
                (status, agent_id)
            )
            await db.commit()
        finally:
            await db.close()

        if agent_id in self.agents:
            self.agents[agent_id].status = status

    async def update_room(self, agent_id: str, room: str):
        """Update which room an agent is in."""
        db = await get_db()
        try:
            await db.execute(
                "UPDATE agents SET current_room = ? WHERE id = ?",
                (room, agent_id)
            )
            await db.commit()
        finally:
            await db.close()

    async def send_message_to_agent(self, agent_id: str, message: str) -> str:
        """Send a message to an agent and get a response.
        
        For now this is a placeholder — will be connected to actual Hermes
        instances in a later iteration.
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            return f"Agent {agent_id} not found."

        # Store the user message
        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO messages (from_agent, to_agent, chat_type, content) VALUES (?, ?, ?, ?)",
                ("user", agent_id, "dm", message)
            )
            await db.commit()
        finally:
            await db.close()

        # Placeholder response — will be replaced with actual Hermes integration
        response = f"[{agent['name']}]: I received your message. (Hermes integration pending)"

        # Store agent response
        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO messages (from_agent, to_agent, chat_type, content) VALUES (?, ?, ?, ?)",
                (agent_id, "user", "dm", response)
            )
            await db.commit()
        finally:
            await db.close()

        return response


# Singleton
agent_manager = AgentManager()
