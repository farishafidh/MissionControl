"""API routes for tasks (Kanban)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from mission_control.database import get_db

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    agent_id: str
    title: str
    description: Optional[str] = ""


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


@router.get("/")
async def list_tasks():
    """Get all tasks."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tasks ORDER BY updated_at DESC")
        rows = await cursor.fetchall()
        return {"tasks": [dict(row) for row in rows]}
    finally:
        await db.close()


@router.get("/agent/{agent_id}")
async def get_agent_tasks(agent_id: str):
    """Get all tasks for a specific agent."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE agent_id = ? ORDER BY updated_at DESC",
            (agent_id,)
        )
        rows = await cursor.fetchall()
        return {"tasks": [dict(row) for row in rows]}
    finally:
        await db.close()


@router.post("/")
async def create_task(task: TaskCreate):
    """Create a new task."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO tasks (agent_id, title, description, status) VALUES (?, ?, ?, ?)",
            (task.agent_id, task.title, task.description, "idle")
        )
        await db.commit()
        return {"status": "created", "task_id": cursor.lastrowid}
    finally:
        await db.close()


@router.patch("/{task_id}")
async def update_task(task_id: int, task: TaskUpdate):
    """Update a task's status or details."""
    db = await get_db()
    try:
        updates = []
        values = []
        if task.status:
            updates.append("status = ?")
            values.append(task.status)
        if task.title:
            updates.append("title = ?")
            values.append(task.title)
        if task.description is not None:
            updates.append("description = ?")
            values.append(task.description)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(task_id)

        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        await db.execute(query, values)
        await db.commit()
        return {"status": "updated"}
    finally:
        await db.close()


@router.delete("/{task_id}")
async def delete_task(task_id: int):
    """Delete a task."""
    db = await get_db()
    try:
        await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()
        return {"status": "deleted"}
    finally:
        await db.close()
