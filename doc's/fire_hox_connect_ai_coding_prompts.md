# FireHox Connect — AI Coding Agent Prompts (Sequential Execution)

## SYSTEM INSTRUCTION (APPLY TO ALL STEPS)

You are a senior full-stack engineer.

Rules:
- Follow instructions EXACTLY
- Do NOT add extra features
- Do NOT refactor unrelated code
- Do NOT change architecture decisions
- Always return complete, working code
- Use exact versions specified
- Use modular structure
- Validate all inputs/outputs

If unclear → assume minimal implementation

---

# PHASE 0 — SETUP

## PROMPT 1: Monorepo Setup

Create a project with the following structure:

/frontend (Next.js 14)
/backend (FastAPI Python 3.11)

Requirements:
- Initialize both projects
- Setup basic README
- Ensure both can run independently

Output:
- Folder structure
- Install commands

---

## PROMPT 2: Backend Base Setup

Create FastAPI app with:
- main.py
- basic route (/health)
- uvicorn config

Requirements:
- Use async endpoints
- Clean folder structure

---

# PHASE 1 — BACKEND CORE

## PROMPT 3: WebSocket Server

Implement WebSocket endpoint:

/ws

Requirements:
- Accept connections
- Broadcast messages
- Maintain connection list

---

## PROMPT 4: Transcript API

Create endpoint:
POST /transcript

Input JSON:
{
  "text": string,
  "speaker": string
}

Requirements:
- Validate input
- Log received data

---

## PROMPT 5: Intent Detection (OpenAI)

Implement function:
- Input: text
- Output: strict JSON

Schema:
{
  "intent": "create_task",
  "confidence": float,
  "entities": {
    "title": string,
    "assignee": string,
    "deadline": string
  }
}

Requirements:
- Use OpenAI GPT-4o-mini
- Enforce JSON output
- Retry once if invalid

---

## PROMPT 6: Pydantic Validation

Create Pydantic models for:
- Intent
- Entities

Requirements:
- Validate all LLM outputs
- Raise errors if invalid

---

## PROMPT 7: Rules Engine

Create deterministic mapping:

FEATURE_HOURS = {
  "login": 20,
  "payment": 20
}

Function:
- Input: title
- Output: estimated_hours

---

## PROMPT 8: Draft Generator

Create function:
- Input: intent + rules
- Output draft object

Structure:
{
  id,
  type,
  title,
  assignee,
  deadline,
  status
}

---

## PROMPT 9: WebSocket Integration

On draft creation:
- Send event to connected clients

Event:
NEW_DRAFT

---

## PROMPT 10: Approval API

POST /approve-draft

Input:
{
  "draft_id": string
}

Requirements:
- Update status to approved

---

# PHASE 2 — FRONTEND

## PROMPT 11: Next.js Setup

Create Next.js app with:
- Tailwind setup
- Basic layout

---

## PROMPT 12: Layout UI

Create layout:
- Video area (placeholder)
- Right sidebar

---

## PROMPT 13: WebSocket Client

Connect to backend WebSocket

Requirements:
- Listen for NEW_DRAFT

---

## PROMPT 14: State Management

Use Zustand

Store:
- drafts array

---

## PROMPT 15: Draft Sidebar

Render list of drafts

Each draft:
- title
- assignee
- deadline

---

## PROMPT 16: Approve Action

Button:
- Calls /approve-draft

Update UI accordingly

---

# PHASE 3 — VIDEO + TRANSCRIPTION

## PROMPT 17: LiveKit Integration

Add video component

Requirements:
- Join room
- Show participants

---

## PROMPT 18: Audio + Transcription

Integrate Deepgram

Flow:
- Capture audio
- Send to Deepgram
- Receive transcript

---

## PROMPT 19: Connect Pipeline

Flow:
- Transcript → backend → intent → draft → UI

---

# PHASE 4 — UX POLISH

## PROMPT 20: Animations

Add:
- Draft slide-in
- Approval color change

---

## PROMPT 21: States

Add:
- Empty state
- Loading state

---

# FINAL RULE

DO NOT:
- Add extra features
- Change schema
- Modify architecture

ONLY implement what is specified step-by-step.

---

## FINAL GOAL

Working system where:
User speaks → draft appears → user approves

Nothing else matters.

