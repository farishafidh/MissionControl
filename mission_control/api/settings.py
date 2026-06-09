"""API routes for settings."""

from fastapi import APIRouter
from pydantic import BaseModel

from mission_control.database import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingUpdate(BaseModel):
    value: str


@router.get("/")
async def get_all_settings():
    """Get all settings."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM settings")
        rows = await cursor.fetchall()
        return {"settings": {row["key"]: row["value"] for row in rows}}
    finally:
        await db.close()


@router.get("/{key}")
async def get_setting(key: str):
    """Get a specific setting."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        if row:
            return {"key": key, "value": row["value"]}
        return {"key": key, "value": None}
    finally:
        await db.close()


@router.put("/{key}")
async def update_setting(key: str, body: SettingUpdate):
    """Update a setting value (e.g., idle_chat_frequency)."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, body.value)
        )
        await db.commit()
        return {"status": "updated", "key": key, "value": body.value}
    finally:
        await db.close()
