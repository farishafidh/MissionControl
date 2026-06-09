"""Idle Chat Scheduler — triggers agent-to-agent conversations at configurable intervals."""

import asyncio
import random
from datetime import datetime

from mission_control.database import get_db
from mission_control.api.websocket import ws_manager


# Sample idle chat topics — will be expanded later
IDLE_TOPICS = [
    "What are you working on today?",
    "Have you tried any new tools lately?",
    "How's your workload looking?",
    "Did you see anything interesting online?",
    "I'm thinking about grabbing coffee. Want some?",
    "It's pretty quiet today, huh?",
    "I finished my last task. Feels good!",
    "Any plans for after work?",
    "I wonder what Faris-kun is working on right now.",
    "Should we organize the shared files?",
    "I learned something new today — want to hear about it?",
    "The weather looks nice outside.",
    "Do you ever take breaks? I feel like I should.",
    "Let's do something fun after this.",
    "What kind of music do you listen to while working?",
]

# Sample responses — placeholder until actual Hermes integration
IDLE_RESPONSES = [
    "Not much, just relaxing for a bit.",
    "Yeah, I was just thinking the same thing!",
    "Sounds good to me~",
    "Hmm, I'm not sure. Let me think about it.",
    "Oh really? Tell me more!",
    "Ha, that's funny. I was about to say the same.",
    "I'm just waiting for the next task.",
    "Sure, why not?",
    "That's interesting! I didn't know that.",
    "Same here. It's been a chill day.",
]


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
        """Generate an idle chat exchange between agents."""
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

            # Generate conversation
            topic = random.choice(IDLE_TOPICS)
            response = random.choice(IDLE_RESPONSES)

            timestamp = datetime.now().isoformat()

            # Store messages
            await db.execute(
                "INSERT INTO messages (from_agent, to_agent, chat_type, content) VALUES (?, ?, ?, ?)",
                (agent_a["id"], "group", "group", topic)
            )
            await db.execute(
                "INSERT INTO messages (from_agent, to_agent, chat_type, content) VALUES (?, ?, ?, ?)",
                (agent_b["id"], "group", "group", response)
            )
            await db.commit()

            # Broadcast to connected WebSocket clients
            await ws_manager.broadcast({
                "type": "group_chat",
                "messages": [
                    {
                        "from_agent": agent_a["id"],
                        "from_name": agent_a["name"],
                        "content": topic,
                        "timestamp": timestamp,
                        "chat_type": "group"
                    },
                    {
                        "from_agent": agent_b["id"],
                        "from_name": agent_b["name"],
                        "content": response,
                        "timestamp": timestamp,
                        "chat_type": "group"
                    }
                ]
            })

            print(f"[IdleChat] {agent_a['name']}: {topic}")
            print(f"[IdleChat] {agent_b['name']}: {response}")

        finally:
            await db.close()


# Singleton
idle_scheduler = IdleChatScheduler()
