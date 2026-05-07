# FireHox Connect — Product Requirements Document (PRD)

## 1. Overview
FireHox Connect is a real-time video workspace that converts live meeting conversations into structured, actionable drafts (tasks) during the meeting itself.

The system listens to conversations, detects actionable intent, and generates draft actions (e.g., tasks) in real-time. These drafts are displayed in a sidebar where users can review, edit, and approve them.

The system does NOT execute actions automatically. All actions require explicit user approval.

---

## 2. Problem Statement
Current video conferencing platforms (Zoom, Google Meet, Microsoft Teams) only facilitate communication. They do not convert conversations into structured work.

After meetings, users must manually:
- Create tasks
- Assign responsibilities
- Send follow-ups
- Schedule next steps

This results in:
- Lost context
- Missed tasks
- Increased manual workload

---

## 3. Product Vision
"Work should be structured during the meeting, not after it."

FireHox Connect acts as an execution layer on top of video calls, transforming spoken intent into structured drafts in real-time.

---

## 4. Core Use Case (MVP)
Primary focus: Dev team task creation (Jira-style workflow)

Example:
User says: "Rahul, finish the login page by tomorrow"

System:
- Detects task intent
- Extracts entities (title, assignee, deadline)
- Generates a draft task
- Displays it in UI
- Waits for user approval

---

## 5. In Scope (MVP)

### 5.1 Core Features
- Video meeting (via LiveKit)
- Real-time transcription (chunked)
- Intent detection (task creation only)
- Draft generation (task)
- Real-time UI updates (WebSocket)
- Draft editing
- Manual approval system
- Draft persistence (Supabase)

### 5.2 Supported Intent Types
- create_task ONLY

### 5.3 UI Scope
- Video panel
- Sidebar with draft cards
- Edit + approve actions

---

## 6. Out of Scope (MVP)

The following are explicitly excluded:
- Automatic execution without approval
- Multi-agent systems
- Email automation
- Calendar scheduling
- RAG / document retrieval
- Multi-intent detection
- Complex workflow orchestration
- Enterprise features

---

## 7. Functional Requirements

### 7.1 Transcription
- Convert audio to text in real-time
- Chunk interval: 2–3 seconds

### 7.2 Intent Detection
- Detect "create_task" intent
- Extract:
  - title
  - assignee
  - deadline
- Return structured JSON

### 7.3 Confidence Handling
- Only process intents with confidence >= 0.7
- Ignore low-confidence outputs

### 7.4 Draft Generation
- Generate structured draft object
- Assign unique ID
- Store status: pending

### 7.5 Real-Time Sync
- Push new drafts instantly to UI

### 7.6 Approval Flow
- User can:
  - Edit draft
  - Approve draft
- On approval:
  - Mark as approved
  - Save in DB

---

## 8. Non-Functional Requirements

### 8.1 Latency
- Draft generation must occur within 2–3 seconds

### 8.2 Reliability
- System must not crash on invalid AI output
- Retry mechanism for malformed responses

### 8.3 Scalability (MVP Level)
- Support small teams (5–10 concurrent users)

### 8.4 Accuracy
- Intent detection accuracy target: 70–80%

---

## 9. Success Criteria

### 9.1 Demo Success Metrics
- Draft appears within 3 seconds
- Correct intent detection for basic tasks
- Smooth UI updates
- No system crashes during demo

### 9.2 Product Validation
- Users can create tasks without leaving meeting
- Reduced manual post-meeting work

---

## 10. Failure Conditions

The product is considered failed if:
- Draft latency > 5 seconds
- Frequent incorrect drafts
- UI is confusing or cluttered
- System auto-executes without approval

---

## 11. Assumptions
- Users speak clearly and include actionable language
- Assignee names are recognizable
- Deadlines are simple (e.g., "tomorrow")

---

## 12. Future Scope (Post-MVP)

Phase 2:
- Draft editing improvements
- PDF/document generation
- Meeting timeline view

Phase 3:
- Scheduler (calendar integration)
- Email drafts
- Knowledge retrieval (RAG)
- Multi-intent detection

---

## 13. Constraints
- Must use LiveKit for video
- Must use FastAPI for backend
- Must use Supabase for DB
- Must use GPT-4o-mini for intent detection

---

## 14. Key Risks

### 14.1 AI Misinterpretation
- Incorrect intent detection

### 14.2 Latency Issues
- Slow transcription or processing

### 14.3 Overengineering
- Building unnecessary features

### 14.4 UI Complexity
- Users unable to understand drafts

---

## 15. Final Definition
FireHox Connect (MVP) is a system that converts spoken task instructions into structured draft tasks in real-time within a video meeting, requiring user approval before execution.

