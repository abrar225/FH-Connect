# FireHox Connect — Implementation Plan (Step-by-Step Build Sequence)

## 1. Overview

This plan defines the exact execution order for building the MVP.

Principles:
- Strict sequential build
- Validate each step before moving forward
- No parallel feature development
- Each module must be testable in isolation

---

## 2. Phase 0 — Project Setup (Foundation)

### Step 1: Monorepo Setup
- Create project structure:

/frontend (Next.js)
/backend (FastAPI)

### Step 2: Environment Setup
- Setup .env files
- Configure:
  - OpenAI key
  - Deepgram key
  - Supabase
  - LiveKit

### Step 3: Basic Dev Setup
- Install dependencies
- Setup linting + formatting

---

## 3. Phase 1 — Backend Core (NO UI YET)

### Step 4: FastAPI Server
- Initialize FastAPI app
- Setup routes structure
- Test basic endpoint

---

### Step 5: WebSocket Server
- Create WebSocket endpoint
- Test connection via simple client

---

### Step 6: Transcript Ingestion API
- POST /transcript
- Accept chunk input

Test:
- Send manual text → verify received

---

### Step 7: Intent Detection Module

- Integrate OpenAI (GPT-4o-mini)
- Define strict JSON schema

Test:
Input:
"Rahul finish login page tomorrow"

Output:
Valid JSON with intent + entities

---

### Step 8: Schema Validation Layer

- Use Pydantic models
- Reject invalid responses
- Retry once if needed

---

### Step 9: Rules Engine

- Implement deterministic logic
- Map features → hours

Test:
Input → expected structured output

---

### Step 10: Draft Generation Module

- Convert intent → draft object

---

### Step 11: WebSocket Push

- On draft creation → send to client

Test:
- Simulate transcript → receive draft via WS

---

### Step 12: Database Integration (Supabase)

- Create tables
- Insert draft records
- Fetch drafts

---

### Step 13: Approval API

- POST /approve-draft
- Update draft status

---

## 4. Phase 2 — Frontend Core (UI + Integration)

### Step 14: Next.js Setup
- Initialize app
- Setup Tailwind

---

### Step 15: Layout System

- Create main layout:
  - Video area (placeholder)
  - Sidebar

---

### Step 16: WebSocket Client

- Connect to backend
- Listen for events

---

### Step 17: Draft State Management

- Zustand store
- Store drafts[]

---

### Step 18: Draft Sidebar UI

- Render list of drafts
- Basic card UI

---

### Step 19: Draft Interaction

- Edit functionality
- Approve button

---

### Step 20: API Integration

- Connect approve API

---

## 5. Phase 3 — Video + Real-Time Integration

### Step 21: LiveKit Integration

- Join room
- Render video

---

### Step 22: Audio Capture

- Extract audio stream

---

### Step 23: Deepgram Integration

- Send audio → get transcript

---

### Step 24: Pipeline Connection

- Transcript → backend → draft → UI

Test Full Flow:
Speak → draft appears

---

## 6. Phase 4 — UX Refinement

### Step 25: Animations
- Draft slide-in
- Approval transitions

---

### Step 26: Loading States
- "Listening..."

---

### Step 27: Empty States
- "No actions detected"

---

## 7. Phase 5 — Demo Readiness

### Step 28: Error Handling
- Retry logic
- Fallback behavior

---

### Step 29: Performance Testing
- Ensure <3s latency

---

### Step 30: Demo Script Validation
- Test full demo flow

---

## 8. Testing Strategy

- Unit test: intent + rules
- Integration test: transcript → draft
- Manual test: UI flow

---

## 9. Build Rules (CRITICAL)

- Do not build multiple modules together
- Validate each step before proceeding
- Do not optimize early
- Do not add extra features

---

## 10. Final Execution Order

1. Backend core
2. Frontend UI
3. Video + audio
4. UX polish
5. Demo readiness

---

## 11. Final Definition

If followed correctly:
- You will have a working MVP
- System will be stable
- Demo will be convincing

If not:
- You will end up with broken integrations and wasted time

