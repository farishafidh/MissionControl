# Mission Control AI — Project Notes & Architecture Plan

## Project Overview
A web-based virtual office for AI agents. Think of it as a living workspace where
AI agents exist, work, and interact — both with Faris (the user) and with each other.
Like managing a small team of real coworkers.

## Core Features

### 1. Individual Agent Chat (Priority: HIGH)
- Chat with any agent individually (like DMs with each coworker)
- Each agent has its own personality, memory, and ongoing tasks
- Agents respond in character

### 2. Agent-to-Agent Group Chat (Priority: HIGH)
- Agents talk to each other autonomously
- Can be work-related or casual (just like real office workers)
- Configurable frequency (how often they chat when idle)
- User can observe/read the chat

### 3. Kanban Dashboard (Priority: HIGH)
- Each agent posts what they're working on
- Status: idle, in progress, finished
- Visual board showing all tasks across all agents

### 4. Virtual Office View (Priority: LOW — do last)
- Visual representation of rooms: office, pantry/break room, meeting room, etc.
- See which agent is "in" which room based on their current activity
- Idle agents might be in the break room chatting
- Working agents at their desk
- Collaborative tasks might show agents in the meeting room

### 5. Always Running (Background)
- Agents are always alive in the background
- When idle: they chat with each other, do nothing, or "hang out"
- When assigned task: they work on it and update the kanban
- Idle chat frequency is configurable by user

## Constraints
- Must work on Windows 11
- Web app (runs in browser, served locally)
- Start with 3 agents
- All Hermes instances (for now — Kiro-CLI possible later)
- Interactive development — Rin will communicate ideas as they come up

## Architecture (Draft v0.1)

### Tech Stack (Proposed)
- Frontend: React or Vue (web dashboard UI)
- Backend: Python (FastAPI or Flask) — orchestrates agents
- Database: SQLite (simple, no setup needed)
- Agent Runtime: Hermes CLI instances (background processes)
- Communication: WebSocket (real-time chat updates to browser)

### System Components

```
┌──────────────────────────────────────────────────────┐
│                   WEB BROWSER (UI)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ Agent    │ │ Group    │ │ Kanban   │ │ Virtual │ │
│  │ Chat     │ │ Chat     │ │ Board    │ │ Office  │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬────┘ │
└───────┼─────────────┼────────────┼────────────┼──────┘
        │             │            │            │
        └─────────────┴──────┬─────┴────────────┘
                             │ WebSocket + REST API
                             │
┌────────────────────────────┴─────────────────────────┐
│              BACKEND SERVER (Python/FastAPI)           │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ Agent       │  │ Chat        │  │ Task/Kanban  │  │
│  │ Manager     │  │ Router      │  │ Manager      │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         │                │                 │          │
│  ┌──────┴─────────────────┴─────────────────┴──────┐  │
│  │           Scheduler / Idle Loop                  │  │
│  │   (triggers agent-to-agent chat at intervals)    │  │
│  └──────────────────────┬──────────────────────────┘  │
└─────────────────────────┼────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │ Agent 1 │      │ Agent 2 │      │ Agent 3 │
   │ (Hermes)│      │ (Hermes)│      │ (Hermes)│
   └─────────┘      └─────────┘      └─────────┘
   Background        Background        Background
   Process           Process           Process
```

### Agent Lifecycle
1. Server starts → spawns 3 Hermes instances (background)
2. Each agent gets a personality/role assigned
3. Idle loop checks schedule → triggers agent-to-agent chat at set intervals
4. When user sends message to an agent → routes to that specific instance
5. Agents update their task status → pushed to kanban via backend
6. UI receives updates via WebSocket in real-time

### Data Model (SQLite)

- **agents** — id, name, personality, status (idle/working/chatting), current_room
- **messages** — id, from_agent, to_agent (or "group"), content, timestamp, chat_type (dm/group)
- **tasks** — id, agent_id, title, description, status (idle/in_progress/done), created_at, updated_at
- **rooms** — id, name, type, agents_present (for virtual office view)
- **settings** — key, value (idle_chat_frequency, etc.)

### Agent Personalities (3 starter agents — TBD)
- Agent 1: ???
- Agent 2: ???
- Agent 3: ???
(Faris to decide what roles/personalities each agent has)

## Decisions Made
- Agent personalities: TBD (decide last, before Feature #4 Virtual Office)
  - Hypothetical concept: Rin as the delegating agent, other agents are her "sisters"
  - To be finalized later
- Idle chat frequency: UI slider (user adjustable)
- Visual style: Dark mode, cozy, not too minimal. NOT anime-inspired.
- Agent task awareness: YES — agents can see each other's tasks and comment on them

## Open Questions
- What personalities/roles should the 3 agents have? (deciding later)
- What should idle chat topics look like? Random? Based on recent tasks? Both?
- Should the user be able to "walk into" a room in the virtual office and join a conversation?
- Token budget management — how to limit idle chat costs?

## Development Phases (Proposed)

### Phase 1 — Foundation ✅
- ✅ Backend server (FastAPI)
- ✅ Basic REST API
- ✅ SQLite database setup
- ⏳ Agent spawning (3 Hermes instances as real background processes) — deferred to Phase 2B

### Phase 2 — Chat System ✅ (skeleton)
- ✅ Individual agent chat (user ↔ agent DMs) — structure works, placeholder responses
- ✅ Group chat (agent ↔ agent) — structure works, placeholder responses
- ✅ Idle chat scheduler (configurable frequency via slider)
- ✅ WebSocket for real-time updates

### Phase 2B — Agent Brain (TODO)
- Connect real Hermes instances to each agent (actual AI responses)
- Idle chat generated by LLM, not random lines
- Agent self-reporting status to kanban

### Phase 3 — Kanban Board ✅
- ✅ Task CRUD (create, update, complete, delete)
- ✅ Visual kanban in the UI with status transitions
- ⏳ Agent self-reporting status — deferred to Phase 2B

### Phase 4 — Web UI ✅
- ✅ Dashboard layout (dark mode, cozy, purple accents)
- ✅ Chat interface (group + DM tabs)
- ✅ Kanban board view with task actions
- ✅ Settings panel (frequency slider)
- NOTE: Built with vanilla HTML/CSS/JS (not React/Vue — simpler for prototype)

### Phase 5 — Virtual Office (Last)
- Room visualization
- Agent location based on activity
- Animations/visual flair
- Requires: rooms table in database

## Notes
- Start simple, iterate
- Rin builds it, Faris reviews and gives direction
- Ideas welcome anytime from both sides
