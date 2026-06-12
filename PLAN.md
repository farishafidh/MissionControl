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

### Agent Personalities (Decided)
- Agent 1 — **Rin (リン)**: Onee-san. Delegator. Affectionate, lightly yandere. Profile: `default`
- Agent 2 — **Mei (芽衣)**: Diligent, precise, reliable. Formal-leaning. Profile: `mei`
- Agent 3 — **Yui (結)**: Cheerful, curious, talkative. The energy of the group. Profile: `yui`
(Full details in AGENTS.md)

## Decisions Made
- Agent personalities: DECIDED — Rin (delegator), Mei (diligent), Yui (cheerful). Three sisters.
- Idle chat frequency: UI slider (user adjustable)
- Visual style: Dark mode, cozy, not too minimal. NOT anime-inspired.
- Agent task awareness: YES — agents can see each other's tasks and comment on them
- Tech stack: Python FastAPI + vanilla HTML/CSS/JS (not React/Vue — simpler for prototype)
- Agent runtime: Hermes profiles (one-shot `-q` calls via subprocess, threaded for Windows)
- Port: 8600 (8000 used by Kiro Gateway, 8500 had zombie processes)

## Open Questions
- What should idle chat topics look like? Random? Based on recent tasks? Both?
- Should the user be able to "walk into" a room in the virtual office and join a conversation?
- Token budget management — frequency slider controls cost for now, but may need daily cap later
- Agent self-reporting: how should agents know about and update their own tasks?
- UI improvement: name indicators on chat bubbles (noted by Faris)

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

### Phase 2B — Agent Brain ✅
- ✅ Created Hermes profiles for Mei and Yui (with SOUL.md personalities)
- ✅ Connected real Hermes instances to each agent (subprocess + threading on Windows)
- ✅ Idle chat scheduler upgraded to use real LLM-generated conversation
- ⏳ Agent self-reporting status to kanban — still TODO

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

## Next Steps (Prioritized)
1. ~~UI fix: Group Chat scrollbar~~ ✅ DONE
2. ~~UI fix: Chat name indicators~~ ✅ DONE
3. ~~UI fix: Chat history loading~~ ✅ DONE (now loads 200 messages)
4. **Agent self-reporting** — Agents update their own task status on kanban
5. ~~Rin as delegator~~ ✅ DONE
6. ~~Conversation persistence~~ ✅ DONE
7. **UI research** — Look at other projects for design inspiration (Faris will research)
8. **Phase 5: Virtual Office** — Room visualization (lowest priority)

## Notes
- Start simple, iterate
- Rin builds it, Faris reviews and gives direction
- Ideas welcome anytime from both sides

## Faris's Notes
- On the group chat currently there's no indicator who's sending the messages. Adding a name above the chat bubble or something will be good
- The current UI is ok, but I think I will research other's project of how their UI looks like. But, sending a screenshot through CLI is impossible...
- The Group Chat (this is the only one that I have checked) need to have something like a scrollbar, because when I scroll to see the chat, the other UI got... uh... submerged above. Then, it would be great to able to see even more earlier chat. A few hours ago, I see the chat from 05.30 PM until 11.00 PM yesterday, but now when I checked again, the chat starts from 00.10 AM until just a while ago.
- Regarding the Conversation Persistence, is it too hard to make that the idle chat between agents sometimes talk about work that assigned to them or like spilling what I DM'd them (when sisters trying to mess with each other / or just anything really)?
