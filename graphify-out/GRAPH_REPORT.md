# Graph Report - FH-Connect  (2026-05-07)

## Corpus Check
- 139 files · ~49,297 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 854 nodes · 1218 edges · 80 communities (71 shown, 9 thin omitted)
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 249 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8d0deee0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 54|Community 54]]

## God Nodes (most connected - your core abstractions)
1. `Event` - 44 edges
2. `authFetch()` - 32 edges
3. `AuthUser` - 27 edges
4. `EventTypes` - 24 edges
5. `require_meeting_admin()` - 18 edges
6. `TaskDraft` - 16 edges
7. `FireHox Connect — Tech Stack Document (Exact Versions)` - 16 edges
8. `FireHox Connect — Frontend Guidelines (Design System + UI Rules)` - 16 edges
9. `FireHox Connect — App Flow Document` - 16 edges
10. `FireHox Connect — Product Requirements Document (PRD)` - 16 edges

## Surprising Connections (you probably didn't know these)
- `saveIntegration()` --calls--> `authFetch()`  [INFERRED]
  frontend/app/dashboard/settings/page.tsx → frontend/app/lib/api.ts
- `test_admin_permission_rejects_non_admin()` --calls--> `AuthUser`  [INFERRED]
  backend/tests/test_security_hardening.py → backend/app/core/auth.py
- `end_meeting()` --calls--> `enqueue_report_event()`  [INFERRED]
  backend/app/modules/meeting/summary.py → backend/app/workers/report_queue.py
- `LandingPage()` --calls--> `useAuth()`  [INFERRED]
  frontend/app/page.tsx → frontend/app/context/AuthContext.tsx
- `RoomPage()` --calls--> `useAuth()`  [INFERRED]
  frontend/app/room/[roomId]/page.tsx → frontend/app/context/AuthContext.tsx

## Communities (80 total, 9 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (34): patch(), LandingPage(), useAuth(), executeJoin(), handleChange(), handleJoin(), generateMeetingId(), handleNewMeeting() (+26 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (38): lifespan(), main.py — Application factory for FH-Connect Backend.  Responsibilities:   1. In, Import all handler modules to trigger their @bus.on() decorators.      This is t, _register_event_handlers(), create_tables(), debug_meeting(), queue_health(), Temporary diagnostic endpoint - remove in production (+30 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (28): _extract_bearer(), _fetch_supabase_user(), get_current_user(), get_websocket_user(), verify_supabase_token(), process_intent(), Validates the AI intent and returns (action, payload)., detect_intent() (+20 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (43): 10. Dev Tooling, 11. Environment Variables, 12. Version Lock Rules, 13. Constraints, 14. Upgrade Policy, 15. Final Definition, 1. Overview, 2. Frontend (Web) (+35 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (42): 10. Final Execution Order, 11. Final Definition, 1. Overview, 2. Phase 0 — Project Setup (Foundation), 3. Phase 1 — Backend Core (NO UI YET), 4. Phase 2 — Frontend Core (UI + Integration), 5. Phase 3 — Video + Real-Time Integration, 6. Phase 4 — UX Refinement (+34 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (38): 10. Performance Expectations, 11. Final Flow Summary, 12. Non-Goals, 13. Design Philosophy, 14. Future Extensions (Not in MVP), 15. Final Definition, 1. Overview, 2. Global Navigation Structure (+30 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (36): require_meeting_admin(), require_database(), _ai_key_status(), _ai_secret_cipher(), _as_dict(), ask_copilot(), coerce_json_dicts(), create_report_share() (+28 more)

### Community 7 - "Community 7"
Cohesion: 0.2
Nodes (34): ApprovalAction, BaseModel, AuthUser, EventTypes, Standard event type constants used across all modules., Event, Standard event envelope. Every event flowing through the system     carries this, TaskDraft (+26 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (35): 10. Failure Conditions, 11. Assumptions, 12. Future Scope (Post-MVP), 13. Constraints, 14.1 AI Misinterpretation, 14.2 Latency Issues, 14.3 Overengineering, 14.4 UI Complexity (+27 more)

### Community 9 - "Community 9"
Cohesion: 0.06
Nodes (30): FINAL GOAL, FINAL RULE, FireHox Connect — AI Coding Agent Prompts (Sequential Execution), PHASE 0 — SETUP, PHASE 1 — BACKEND CORE, PHASE 2 — FRONTEND, PHASE 3 — VIDEO + TRANSCRIPTION, PHASE 4 — UX POLISH (+22 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (30): 10. Accessibility, 11. UX Rules (CRITICAL), 12. Empty States, 13. Loading States, 14. Error States, 15. Final Definition, 1. Design Philosophy, 2.1 Left Sidebar (+22 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (24): record_audit_event(), new_trace_id(), Generate a new trace ID. Same format as new_id but semantically distinct., require_admin(), create_meeting_record(), get_meeting(), get_report_status(), save_meeting_report() (+16 more)

### Community 12 - "Community 12"
Cohesion: 0.1
Nodes (15): handle_draft_cancelled(), handle_draft_created(), handle_draft_updated(), handle_meeting_admin_updated(), handle_meeting_lock_updated(), handle_pulse_generated(), handle_transcript_received_broadcast(), modules/notification/handlers.py — Event handlers for the Notification domain. (+7 more)

### Community 13 - "Community 13"
Cohesion: 0.1
Nodes (20): code:bash (cd FH-Connect), code:bash (npm run dev), code:bash (cd backend), code:bash (source .venv/bin/activate), code:powershell (.\.venv\Scripts\Activate.ps1), code:bash (pip install -r requirements.txt), code:bash (cp .env.example .env), code:bash (python run.py) (+12 more)

### Community 14 - "Community 14"
Cohesion: 0.1
Nodes (20): 10. Future Extensions, 11. Final Definition, 1. Overview, 2. Database: Supabase (PostgreSQL), 3.1 users, 3.2 meetings, 3.3 meeting_participants, 3.4 transcripts (+12 more)

### Community 15 - "Community 15"
Cohesion: 0.14
Nodes (6): EventBus, core/event_bus.py — Asynchronous Event Bus (Supports Redis)  This is the central, Background task to listen for events from Redis., Invoke all local handlers for the event., Connect to Redis if configured, otherwise use local mode., Clean up Redis connections.

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (11): BaseHTTPMiddleware, get_logger(), get_request_id(), JsonFormatter, core/logging.py — Structured logging for the entire backend.  Provides a consist, Returns a named logger with a consistent format.      Usage:         from app.co, RequestContextFilter, reset_request_id() (+3 more)

### Community 17 - "Community 17"
Cohesion: 0.18
Nodes (14): AuthorizationError, DatabaseUnavailableError, EventBusError, FHConnectError, IntentDetectionError, MeetingNotFoundError, core/exceptions.py — Custom exception hierarchy.  Provides domain-specific excep, Base exception for all FH-Connect errors. (+6 more)

### Community 18 - "Community 18"
Cohesion: 0.13
Nodes (14): 🔐 1. Environment Variables Check, 📦 2. Backend Deployment (FastAPI), 🌐 3. Frontend Deployment (Next.js), 🏗️ 4. Infrastructure Setup, 🛡️ 5. Post-Deployment Verification, Backend (`.env`), code:bash (cd backend), code:bash (uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4) (+6 more)

### Community 19 - "Community 19"
Cohesion: 0.26
Nodes (5): ConnectionManager, Send a message to all connections of a specific user in a room., Cache the latest pulse for a room so late joiners receive it., Broadcast to all connected clients in a specific room., websocket_endpoint()

### Community 20 - "Community 20"
Cohesion: 0.27
Nodes (9): _chain_for_user(), generate_final_report(), generate_summary(), InternalReport, MeetingReport, Generates a comprehensive meeting report at the end of a session., Generates a meeting pulse including status and individual perspectives., get_summary() (+1 more)

### Community 21 - "Community 21"
Cohesion: 0.2
Nodes (9): code:bash (python3.11 -m venv .venv), code:bash (pip install -r requirements.txt -c constraints.txt), code:bash (source .venv/bin/activate), code:bash (source .venv/bin/activate), code:bash (source .venv/bin/activate), FireHox Connect Backend, Run, Setup (+1 more)

### Community 22 - "Community 22"
Cohesion: 0.33
Nodes (5): asRecord(), normalizeSettings(), readApiError(), saveIntegration(), saveSettings()

### Community 23 - "Community 23"
Cohesion: 0.22
Nodes (8): 🤖 AI & Agent Rules, code:text (├── frontend/          # Next.js 14 Frontend Application), 📘 Documentation, 🚀 FireHox Connect, ✨ Key Features, 🚀 Quick Start, 📁 Repository Structure, 🛠️ Tech Stack

### Community 24 - "Community 24"
Cohesion: 0.29
Nodes (7): approve_draft(), DraftResponse, list_pending_drafts(), Rejects a draft by updating its status to 'rejected'.     Broadcasts the status, Lists task drafts in 'pending' status, optionally filtered by room_id., Approves a draft by updating its status to 'approved'.     Broadcasts the status, reject_draft()

### Community 25 - "Community 25"
Cohesion: 0.36
Nodes (4): FakePool, test_get_report_status_returns_status_shape(), test_save_meeting_report_marks_completed(), test_set_report_status_records_queued_timestamp()

### Community 26 - "Community 26"
Cohesion: 0.32
Nodes (3): _request(), test_meeting_ai_health_reports_missing_ai_key(), test_productivity_endpoints_require_authentication()

### Community 27 - "Community 27"
Cohesion: 0.25
Nodes (7): Agent Rules & Mandatory Procedures, code:bash (# Using the project's Python environment), How to Update, How to Use the Graph, 🧠 Knowledge Graph (Graphify), 🚨 Mandatory Requirement, Rules for Agents

### Community 28 - "Community 28"
Cohesion: 0.25
Nodes (7): FireHox Connect — Demo Validation Script, Preparation, Test Phrase 1: Standard Assignment, Test Phrase 2: Status Update + Action Item, Test Phrase 3: Self-Assignment, Test Phrase 4: Complex Multi-part sentence, Test Phrase 5: Vague Deadline

### Community 30 - "Community 30"
Cohesion: 0.33
Nodes (5): _heuristic_insights(), persist_transcript_and_insights(), handle_transcript_received(), modules/transcript/handlers.py — Event handlers for the Transcript domain.  List, Validates an incoming transcript chunk and forwards it for intent detection.

### Community 31 - "Community 31"
Cohesion: 0.6
Nodes (5): _drain_local_queue(), test_local_intent_queue_failure_metrics(), test_local_intent_queue_idempotency(), test_local_intent_queue_metrics(), test_local_intent_queue_round_trip()

### Community 33 - "Community 33"
Cohesion: 0.6
Nodes (5): _request(), test_invalid_content_length_is_rejected(), test_oversized_request_is_rejected(), test_rate_limiter_rejects_after_threshold(), test_request_id_is_returned_to_client()

### Community 34 - "Community 34"
Cohesion: 0.6
Nodes (5): _request(), test_approval_list_requires_authentication(), test_deepgram_token_requires_authentication(), test_livekit_token_requires_authentication(), test_transcript_ingest_requires_authentication()

### Community 35 - "Community 35"
Cohesion: 0.4
Nodes (3): core/config.py — Centralized configuration management.  All environment variable, Application-wide settings derived from environment variables., Settings

### Community 37 - "Community 37"
Cohesion: 0.4
Nodes (4): code:bash (npm run dev), Deploy on Vercel, Getting Started, Learn More

### Community 39 - "Community 39"
Cohesion: 0.5
Nodes (3): new_id(), core/ids.py — ID generation utilities.  Provides consistent ID and trace_id gene, Generate a new UUID4 string.

### Community 40 - "Community 40"
Cohesion: 0.5
Nodes (3): export_task(), ExportRequest, Simulates exporting an approved task to an external platform.     In a real app,

### Community 41 - "Community 41"
Cohesion: 0.5
Nodes (3): handle_intent_detected(), modules/draft/handlers.py — Event handlers for the Draft domain.  Listens to: in, Processes a detected intent into a draft database operation.     Replaces the st

### Community 42 - "Community 42"
Cohesion: 0.5
Nodes (3): modules/transcript/service.py — HTTP API endpoint for transcript ingestion.  Thi, Accepts real-time transcript chunks from the frontend.      This endpoint is int, receive_transcript()

### Community 43 - "Community 43"
Cohesion: 0.5
Nodes (3): Feature-Sliced Design (FSD), Modules, Rules

## Knowledge Gaps
- **311 isolated node(s):** `Backend package for FireHox Connect.`, `main.py — Application factory for FH-Connect Backend.  Responsibilities:   1. In`, `Import all handler modules to trigger their @bus.on() decorators.      This is t`, `core/logging.py — Structured logging for the entire backend.  Provides a consist`, `Returns a named logger with a consistent format.      Usage:         from app.co` (+306 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Event` connect `Community 7` to `Community 1`, `Community 2`, `Community 6`, `Community 41`, `Community 42`, `Community 11`, `Community 15`, `Community 20`, `Community 24`, `Community 30`, `Community 31`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `AuthUser` connect `Community 7` to `Community 24`, `Community 2`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `start_report_worker()` connect `Community 1` to `Community 11`, `Community 7`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 40 inferred relationships involving `Event` (e.g. with `EventTypes` and `TranscriptChunk`) actually correct?**
  _`Event` has 40 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `authFetch()` (e.g. with `handleNewMeeting()` and `saveSettings()`) actually correct?**
  _`authFetch()` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `AuthUser` (e.g. with `TranscriptChunk` and `CreateMeetingReq`) actually correct?**
  _`AuthUser` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `EventTypes` (e.g. with `Event` and `EventBus`) actually correct?**
  _`EventTypes` has 22 INFERRED edges - model-reasoned connections that need verification._