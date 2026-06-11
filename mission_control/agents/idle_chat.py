"""Idle Chat Scheduler — triggers agent-to-agent conversations at configurable intervals."""

import asyncio
import random
from datetime import datetime

from mission_control.database import get_db
from mission_control.api.websocket import ws_manager
from mission_control.agents.manager import agent_manager


class IdleChatScheduler:
    """Schedules periodic agent-to-agent idle conversations."""

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._running = False
        self.frequency_minutes = 15  # default, loaded from settings

    async def start(self):
        """Start the idle chat loop."""
        self._running = True
        await self._load_frequency()
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        """Stop the idle chat loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _load_frequency(self):
        """Load chat frequency from settings."""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT value FROM settings WHERE key = 'idle_chat_frequency'"
            )
            row = await cursor.fetchone()
            if row:
                self.frequency_minutes = int(row["value"])
        finally:
            await db.close()

    async def _loop(self):
        """Main loop — trigger idle chat at intervals."""
        while self._running:
            try:
                await self._load_frequency()

                # If frequency is 0, idle chat is disabled
                if self.frequency_minutes <= 0:
                    await asyncio.sleep(60)  # check again in a minute
                    continue

                await asyncio.sleep(self.frequency_minutes * 60)

                if self._running:
                    await self._trigger_idle_chat()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[IdleChatScheduler] Error: {e}")
                await asyncio.sleep(30)

    async def _trigger_idle_chat(self):
        """Generate an idle chat exchange between agents using real LLM."""
        db = await get_db()
        try:
            # Get idle agents
            cursor = await db.execute(
                "SELECT * FROM agents WHERE status = 'idle'"
            )
            idle_agents = await cursor.fetchall()
            idle_agents = [dict(a) for a in idle_agents]

            if len(idle_agents) < 2:
                return  # Need at least 2 agents to chat

            # Pick 2 random agents
            agent_a, agent_b = random.sample(idle_agents, 2)

            timestamp = datetime.now().isoformat()

            # Agent A starts the conversation
            context = f"{agent_b['name']} is nearby and idle."
            message_a = await agent_manager.generate_idle_chat(agent_a["id"], context)

            if not message_a:
                return

            # Store message A
            await db.execute(
                "INSERT INTO messages (from_agent, to_agent, chat_type, content) VALUES (?, ?, ?, ?)",
                (agent_a["id"], "group", "group", message_a)
            )
            await db.commit()

            # Agent B responds
            context_b = f"{agent_a['name']} just said: \"{message_a}\". Respond naturally and briefly (1-2 sentences)."
            message_b = await agent_manager.generate_idle_chat(agent_b["id"], context_b)

            if not message_b:
                return

            # Store message B
            await db.execute(
                "INSERT INTO messages (from_agent, to_agent, chat_type, content) VALUES (?, ?, ?, ?)",
                (agent_b["id"], "group", "group", message_b)
            )
            await db.commit()

            # Broadcast to connected WebSocket clients
            await ws_manager.broadcast({
                "type": "group_chat",
                "messages": [
                    {
                        "from_agent": agent_a["id"],
                        "from_name": agent_a["name"],
                        "content": message_a,
                        "timestamp": timestamp,
                        "chat_type": "group"
                    },
                    {
                        "from_agent": agent_b["id"],
                        "from_name": agent_b["name"],
                        "content": message_b,
                        "timestamp": timestamp,
                        "chat_type": "group"
                    }
                ]
            })

            print(f"[IdleChat] {agent_a['name']}: {message_a}")
            print(f"[IdleChat] {agent_b['name']}: {message_b}")

        finally:
            await db.close()


# Singleton
idle_scheduler = IdleChatScheduler()
