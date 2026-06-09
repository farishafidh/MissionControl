# Mission Control AI

A web-based virtual office for AI agents. Manage, observe, and interact with your AI agent team from a cozy dark-mode dashboard.

## Features (Planned)

- **Individual Agent Chat** — DM any agent directly
- **Agent-to-Agent Group Chat** — watch your agents talk to each other (configurable frequency)
- **Kanban Dashboard** — see what each agent is working on (idle / in progress / done)
- **Virtual Office View** — visual rooms showing where agents "are" (coming later)
- **Always Running** — agents live in the background, chatting and working

## Tech Stack

- **Backend:** Python (FastAPI) + SQLite
- **Frontend:** Web app (dark mode, cozy aesthetic)
- **Agents:** Hermes Agent instances
- **Real-time:** WebSocket

## Status

🚧 Early development — Phase 1 (Foundation)

## Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m mission_control.main
```

## License

MIT
