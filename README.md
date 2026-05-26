# 🚀 FireHox Connect

[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

**FireHox Connect** is a cutting-edge real-time AI meeting assistant designed to transform your conversations into actionable insights. Leveraging state-of-the-art LLMs (Gemini 2.5, Llama 3.3) and high-fidelity transcription, FireHox Connect captures every detail, detects meeting items in real-time, and provides a sleek, modern UI for maximum productivity.

![FireHox Connect Demo](./fh_connect_hero_1775119672332.png)

## ✨ Key Features

- **🔴 Real-time Transcription**: Powered by Deepgram for lightning-fast and accurate speech-to-text.
- **🧠 Multi-model Intelligence**: Pluggable architecture supporting Gemini 2.5 Flash and Llama 3.3 (via Groq) for high-performance reasoning.
- **⚡ Real-time Feedback Loop**: Instant "Meeting Pulse" and AI-driven action item detection.
- **🎨 Premium UI/UX**: Modern dark-themed dashboard built with Next.js, Framer Motion, and Tailwind CSS.
- **🔌 Robust Backend**: High-performance FastAPI backend with WebSocket support for low-latency communication.
- **🏢 Managed Infrastructure**: Seamless integration with Supabase for authentication/database and LiveKit for media streaming.

## 📁 Repository Structure

```text
├── frontend/          # Next.js 14 Frontend Application
├── backend/           # FastAPI Python 3.11 Backend API
├── scripts/           # Automation and utility scripts
└── doc's/             # Project documentation and architectural references
```

## 🛠️ Tech Stack

- **Frontend**: Next.js, React, TypeScript, Tailwind CSS, Framer Motion, Zustand.
- **Backend**: Python 3.11, FastAPI, LangChain, LangGraph, Uvicorn.
- **Services**: Supabase (DB/Auth), LiveKit (WebRTC), Deepgram (STT), Groq/Google (LLMs).

## 🚀 Quick Start

Looking to get up and running quickly? 

1. **Clone/Download**: Extract the project files to your local machine.
2. **Setup**: Follow our detailed walkthrough in the [**INSTALL.md**](./INSTALL.md) file.
3. **Run**:
   - Backend: `python run.py` (inside `backend` with venv active)
   - Frontend: `npm run dev` (inside `frontend`)

## 📘 Documentation

For deep-dives into the architecture, design, and implementation:
- [**Installation Guide**](./INSTALL.md) - **Start Here!**
- [**Product Requirements (PRD)**](./doc%27s/fire_hox_connect_prd.md)
- [**Tech Stack Reference**](./doc%27s/fire_hox_connect_tech_stack.md)
- [**Implementation Plan**](./doc%27s/fire_hox_connect_implementation_plan.md)
- [**Database Schema**](./doc%27s/fire_hox_connect_backend_schema.md)
- [**App User Flow**](./doc%27s/fire_hox_connect_app_flow.md)
- [**Frontend Guidelines**](./doc%27s/fire_hox_connect_frontend_guidelines.md)

## 🤖 AI & Agent Rules

This repository is optimized for AI coding assistants using **Graphify**. 

- **Knowledge Graph**: A pre-built graph is available in `graphify-out/`.
- **Mandatory Procedure**: All AI agents MUST run `backend/.venv/bin/graphify update .` after any code changes.
- **Rules**: See [**AGENT_RULES.md**](./AGENT_RULES.md) for full instructions.

---

Developed with ❤️ by the FireHox Team.
<!-- [2025-01-23T18:11:50] docs(readme): update project documentation and overview -->
<!-- [2025-03-03T21:17:00] docs(readme): update project documentation and overview -->
<!-- [2025-03-27T18:40:24] style: improve formatting and badge alignment -->
<!-- [2025-04-09T09:23:31] docs(readme): update project documentation and overview -->
<!-- [2025-06-10T12:28:29] docs(readme): update project documentation and overview -->
<!-- [2025-06-27T22:37:23] style: improve formatting and badge alignment -->
<!-- [2025-07-01T12:33:23] style: improve formatting and badge alignment -->
<!-- [2025-08-02T22:44:34] docs(readme): update project documentation and overview -->
<!-- [2025-10-16T10:28:03] docs(readme): update project documentation and overview -->
<!-- [2025-11-19T11:01:30] docs(readme): update project documentation and overview -->
<!-- [2026-01-07T11:48:56] docs(readme): update project documentation and overview -->
<!-- [2026-01-16T12:32:17] style: improve formatting and badge alignment -->
<!-- [2026-02-08T19:03:31] style: improve formatting and badge alignment -->
<!-- [2026-02-08T22:36:29] style: improve formatting and badge alignment -->
<!-- [2026-02-17T18:09:24] style: improve formatting and badge alignment -->
<!-- [2026-03-03T22:54:00] style: improve formatting and badge alignment -->
<!-- [2026-03-13T11:15:42] docs(readme): update project documentation and overview -->
<!-- [2026-03-30T18:47:20] docs(readme): update project documentation and overview -->
<!-- [2026-05-06T16:54:02] style: improve formatting and badge alignment -->
<!-- [2026-05-26T20:51:07] docs(readme): update project documentation and overview -->
