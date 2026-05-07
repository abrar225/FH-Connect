# FireHox Connect — Tech Stack Document (Exact Versions)

## 1. Overview
This document defines the exact technologies, libraries, APIs, and versions used in FireHox Connect MVP.

Principles:
- Stability over novelty
- Minimal dependencies
- Strict version locking (no ^ or ~)

---

## 2. Frontend (Web)

### Core Framework
- Next.js: 14.1.3
- React: 18.2.0
- React DOM: 18.2.0

### Styling
- Tailwind CSS: 3.4.1
- PostCSS: 8.4.35
- Autoprefixer: 10.4.17

### UI Utilities
- clsx: 2.1.0
- tailwind-merge: 2.2.1

### State Management
- Zustand: 4.5.2

### Real-time / Networking
- socket.io-client: 4.7.5 (only if needed fallback)
- native WebSocket API (primary)

### Video SDK
- livekit-client: 2.1.0

---

## 3. Mobile (Future — Not in MVP)

- React Native (Expo): 50.0.6
- expo: 50.0.6

(Not implemented in MVP)

---

## 4. Backend (Core System)

### Framework
- FastAPI: 0.110.0
- Uvicorn: 0.27.1

### Python Version
- Python: 3.11.8

### Async + Utilities
- pydantic: 2.6.3
- python-dotenv: 1.0.1

### WebSocket
- starlette: 0.36.3

---

## 5. AI / LLM Layer

### OpenAI
- openai: 1.14.3
- Model: gpt-4o-mini

### Orchestration
- langchain: 0.1.14
- langgraph: 0.0.34

---

## 6. Transcription

### Primary
- Deepgram SDK: 3.2.0

### Fallback
- Web Speech API (browser native)

---

## 7. Database & Backend Services

### Supabase
- supabase-js: 2.39.3

### Database
- PostgreSQL (via Supabase)

### Auth
- Supabase Auth (not heavily used in MVP)

---

## 8. Realtime Messaging

### Primary
- Native WebSocket (FastAPI)

### Optional
- Redis (future scaling)

---

## 9. Deployment

### Frontend
- Vercel (latest stable runtime)

### Backend
- Railway (Docker-based deployment)

### Database
- Supabase (hosted)

---

## 10. Dev Tooling

### Package Managers
- npm: 10.5.0
- pip: 24.0

### Linting / Formatting
- ESLint: 8.57.0
- Prettier: 3.2.5

### Type Safety
- TypeScript: 5.4.2

---

## 11. Environment Variables

### Frontend
- NEXT_PUBLIC_LIVEKIT_URL
- NEXT_PUBLIC_SUPABASE_URL
- NEXT_PUBLIC_SUPABASE_ANON_KEY

### Backend
- OPENAI_API_KEY
- DEEPGRAM_API_KEY
- SUPABASE_SERVICE_ROLE_KEY
- DATABASE_URL

---

## 12. Version Lock Rules

- No caret (^)
- No tilde (~)
- All dependencies pinned exactly
- Lockfile must be committed

---

## 13. Constraints

- Must use LiveKit for video
- Must use FastAPI for backend
- Must use Supabase for DB
- Must use GPT-4o-mini for intent detection

---

## 14. Upgrade Policy

- No upgrades during MVP build
- Only upgrade after stable release

---

## 15. Final Definition

This stack is optimized for:
- Fast development
- Real-time processing
- Stability during demo

No experimental or unstable tools are included.

