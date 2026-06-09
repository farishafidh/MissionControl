"""API routes for messages/chat."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from mission_control.database import get_db

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("/group")
async def get_group_messages(limit: int = 50):
    """Get recent group chat messages (agent-to-agent)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM messages WHERE chat_type = 'group' ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return {"messages": [dict(row) for row in reversed(rows)]}
    finally:
        await db.close()


@router.get("/dm/{agent_id}")
async def get_dm_messages(agent_id: str, limit: int = 50):
    """Get DM messages between user and a specific agent."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT * FROM messages 
            WHERE chat_type = 'dm' AND (from_agent = ? OR to_agent = ?)
            ORDER BY timestamp DESC LIMIT ?""",
            (agent_id, agent_id, limit)
        )
        rows = await cursor.fetchall()
        return {"messages": [dict(row) for row in reversed(rows)]}
    finally:
        await db.close()


@router.get("/all")
async def get_all_messages(limit: int = 100):
    """Get all recent messages."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM messages ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return {"messages": [dict(row) for row in reversed(rows)]}
    finally:
        await db.close()
