# FireHox Connect — App Flow Document

## 1. Overview
This document defines the complete user flow, navigation structure, and interaction behavior for the FireHox Connect MVP.

Scope: Single-use-case system (Task Drafting during meetings)
Mode: Demo-first (no complex onboarding friction)

---

## 2. Global Navigation Structure

### Primary Routes
- / (Landing / Entry)
- /meeting/:roomId (Main meeting workspace)

MVP intentionally avoids deep navigation trees.

---

## 3. User Journey (End-to-End)

### Step 1: Entry
User lands on homepage

Actions:
- Enter name
- Click "Join Meeting"

System:
- Generates roomId (if not provided)
- Redirects to /meeting/:roomId

---

### Step 2: Meeting Join
Page: /meeting/:roomId

UI Sections:
1. Video Panel (left / main)
2. Draft Sidebar (right — core USP)

System actions:
- Connect to LiveKit room
- Initialize audio stream
- Start transcription pipeline

---

### Step 3: Live Meeting State

#### 3.1 Transcription Flow
- Audio → transcription module
- Chunked every 2–3 seconds

#### 3.2 Intent Detection Trigger
- Each transcript chunk sent to backend
- Intent module evaluates

If no intent → ignore
If valid intent → proceed

---

### Step 4: Draft Creation

System generates draft object

UI Reaction:
- New draft card appears in sidebar instantly
- Animation: slide-in (right → left)

Draft Card Contains:
- Title
- Assignee
- Deadline
- Status: Pending
- Actions: [Edit] [Approve]

---

### Step 5: Draft Interaction

#### 5.1 Edit Flow
User clicks "Edit"

UI:
- Inline editable fields OR modal

Editable Fields:
- Title
- Assignee
- Deadline

On Save:
- Update draft in frontend state
- Sync to backend

---

#### 5.2 Approve Flow
User clicks "Approve"

System:
- Sends POST /approve-draft

Backend:
- Marks draft as approved
- Stores in database

UI:
- Status changes to "Approved"
- Visual feedback (green highlight / checkmark)

---

### Step 6: Continuous Updates

If user speaks again:
- New draft OR update existing draft

System Behavior:
- If same context → update draft
- If new context → create new draft

---

### Step 7: Meeting End

User leaves meeting

System:
- Disconnect LiveKit
- Stop transcription

(No post-processing in MVP)

---

## 4. Page-Level Breakdown

### 4.1 Landing Page (/)

Elements:
- Minimal UI
- Input: Name
- Button: "Join Meeting"

No distractions, no marketing clutter

---

### 4.2 Meeting Page (/meeting/:roomId)

Layout:

[ Video Panel ] | [ Draft Sidebar ]

#### Video Panel
- LiveKit video grid
- Mute/unmute
- Camera toggle

#### Draft Sidebar (Core Product)
- Scrollable list
- Real-time updates

---

## 5. Component Flow

### Components

- VideoContainer
- DraftSidebar
- DraftCard
- EditDraftModal

---

### Data Flow

WebSocket → Frontend State → UI Render

User Action → API → Backend → DB → UI Update

---

## 6. State Management

Frontend State:
- drafts[]
- connection status
- meeting metadata

No overengineering (no Redux initially)

---

## 7. Edge Cases (MVP Handling)

### 7.1 Low Confidence Intent
- Ignore silently

### 7.2 Invalid AI Output
- Retry once
- If fail → discard

### 7.3 Duplicate Drafts
- Basic deduplication by title + time window

### 7.4 Network Drop
- Attempt reconnect
- Preserve UI state

---

## 8. UX Rules (CRITICAL)

- No popups interrupting meeting
- All actions in sidebar
- No auto-execution
- Minimal clicks

---

## 9. Animation & Feedback

- Draft appear → slide-in
- Approve → color change
- Edit → smooth transition

Keep subtle, not flashy

---

## 10. Performance Expectations

- Draft appears within 2–3 seconds
- UI updates must feel instant (<500ms)

---

## 11. Final Flow Summary

User speaks → System detects → Draft appears → User edits → User approves → Stored

This loop repeats continuously during meeting.

---

## 12. Non-Goals

- No dashboards
- No analytics
- No multi-page complexity

---

## 13. Design Philosophy

- One screen focus
- Sidebar is product
- Video is context

---

## 14. Future Extensions (Not in MVP)

- Multi-draft types
- Timeline view
- Workspace after meeting

---

## 15. Final Definition

The app flow is centered around a single real-time loop:
Conversation → Detection → Draft → Interaction → Approval

Everything else is secondary.

