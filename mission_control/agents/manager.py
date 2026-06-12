"""Agent Manager — handles spawning and managing Hermes agent instances."""

import asyncio
import subprocess
import os
import re
from typing import Optional
from dataclasses import dataclass, field

from mission_control.database import get_db


# Map agent IDs to Hermes profile names
AGENT_PROFILES = {
    "agent-1": "rin",
    "agent-2": "mei",
    "agent-3": "yui",
}

# Map agent IDs to display names
AGENT_NAMES = {
    "agent-1": "Rin",
    "agent-2": "Mei",
    "agent-3": "Yui",
}


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\].*?\x07|\r')
    return ansi_escape.sub('', text)


def extract_response(raw_output: str) -> str:
    """Extract the actual response text from Hermes CLI output."""
    lines = strip_ansi(raw_output).split('\n')
    
    # Find content between the box borders (╭ and ╰)
    in_response = False
    response_lines = []
    
    for line in lines:
        # Detect box start
        if '╭' in line and 'Hermes' in line:
            in_response = True
            continue
        # Detect box end
        if '╰' in line and in_response:
            in_response = False
            continue
        # Collect response lines
        if in_response:
            # Strip the left border character
            cleaned = line.strip()
            if cleaned.startswith('┊'):
                continue  # Skip tool output lines
            response_lines.append(cleaned)
    
    # Join and clean up
    response = '\n'.join(response_lines).strip()
    
    # Fallback: if parsing failed, return raw output trimmed
    if not response:
        # Try to find anything that looks like a response
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith(('Query:', 'Initializing', '─', '╭', '╰', '┊', 'Resume', 'Session:', 'Duration:', 'Messages:')):
                response_lines.append(stripped)
        response = '\n'.join(response_lines).strip()
    
    return response if response else "(No response)"


@dataclass
class AgentProcess:
    """Represents a running agent instance."""
    id: str
    name: str
    personality: str
    profile: str = ""
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

        profile = AGENT_PROFILES.get(agent_id, "default")
        self.agents[agent_id] = AgentProcess(
            id=agent_id,
            name=name,
            personality=personality,
            profile=profile
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
        """Send a message to an agent via its Hermes profile and get a response.
        
        If the agent is Rin (agent-1) and her response contains delegation blocks,
        those are parsed and routed to the appropriate sister agents.
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            return f"Agent {agent_id} not found."

        profile = AGENT_PROFILES.get(agent_id, "rin")

        # Update status to chatting
        await self.update_status(agent_id, "chatting")

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

        # Call Hermes with the agent's profile
        try:
            response = await self._call_hermes(profile, message)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            response = f"(Error communicating with {agent['name']}: {type(e).__name__}: {str(e)}\n{tb})"

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

        # If this is Rin, check for delegation blocks
        if agent_id == "agent-1":
            response = await self._handle_delegation(response)

        # Update status back to idle
        await self.update_status(agent_id, "idle")

        return response

    async def _handle_delegation(self, response: str) -> str:
        """Parse delegation blocks from Rin's response and route to sisters.
        
        Format: [DELEGATE:mei]task here[/DELEGATE]
                [DELEGATE:yui]task here[/DELEGATE]
        """
        import re as regex
        
        delegation_pattern = regex.compile(
            r'\[DELEGATE:(mei|yui)\](.*?)\[/DELEGATE\]',
            regex.DOTALL
        )
        
        matches = delegation_pattern.findall(response)
        if not matches:
            return response

        # Remove delegation blocks from the visible response
        clean_response = delegation_pattern.sub('', response).strip()

        # Process each delegation
        delegation_results = []
        for target_name, task in matches:
            target_id = "agent-2" if target_name == "mei" else "agent-3"
            target_profile = AGENT_PROFILES[target_id]
            
            # Update target agent status
            await self.update_status(target_id, "working")
            
            # Send task to target agent
            delegation_prompt = f"Rin-nee asked you to do this: {task.strip()}"
            try:
                result = await self._call_hermes(target_profile, delegation_prompt)
                delegation_results.append(f"\n\n---\n📋 [{target_name.capitalize()}]: {result}")
            except Exception as e:
                delegation_results.append(f"\n\n---\n📋 [{target_name.capitalize()}]: (Could not reach {target_name})")
            
            # Store delegation message in group chat
            db = await get_db()
            try:
                await db.execute(
                    "INSERT INTO messages (from_agent, to_agent, chat_type, content) VALUES (?, ?, ?, ?)",
                    (target_id, "group", "group", f"Rin-nee asked me to: {task.strip()}")
                )
                await db.commit()
            finally:
                await db.close()
            
            # Update status back
            await self.update_status(target_id, "idle")

        # Combine Rin's response with delegation results
        return clean_response + ''.join(delegation_results)

    async def _call_hermes(self, profile: str, message: str, persist: bool = True) -> str:
        """Call Hermes CLI with a specific profile and return the response.
        
        Args:
            profile: Hermes profile name
            message: Message to send
            persist: If True, uses --continue to maintain conversation history.
                     If False, starts a fresh session (for idle chat).
        """
        hermes_path = os.path.join(
            os.path.expanduser("~"), "AppData", "Local", "hermes",
            "hermes-agent", "venv", "Scripts", "hermes.exe"
        )
        
        if persist:
            cmd = [hermes_path, "chat", "-c", "-q", message, "-p", profile]
        else:
            cmd = [hermes_path, "chat", "-q", message, "-p", profile]

        # Use subprocess.run in a thread — asyncio subprocess has issues on Windows with uvicorn
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    stdin=subprocess.DEVNULL
                )
            )
            return extract_response(result.stdout)
        except subprocess.TimeoutExpired:
            return "(Agent took too long to respond)"
        except Exception as e:
            return f"(Error: {type(e).__name__}: {str(e)})"

    async def generate_idle_chat(self, agent_id: str, context: str = "") -> str:
        """Generate an idle chat message from an agent.
        
        Uses persist=False so idle chatter doesn't pollute the agent's
        main conversation history with the user.
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            return ""

        profile = AGENT_PROFILES.get(agent_id, "default")
        prompt = f"You're hanging out in the office with your sisters. Say something casual — could be about work, a random thought, or just chatting. Keep it short (1-2 sentences). Context: {context}" if context else "You're hanging out in the office with your sisters. Say something casual — could be about work, a random thought, or just chatting. Keep it short (1-2 sentences)."

        try:
            return await self._call_hermes(profile, prompt, persist=False)
        except Exception:
            return ""


# Singleton
agent_manager = AgentManager()
