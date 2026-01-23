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
- [2025-02-26T14:17:33] style: enhance README formatting and badge definitions
- [2025-03-04T14:19:58] docs(readme): improve documentation notes and usage guidelines
- [2025-05-02T17:10:54] style: enhance README formatting and badge definitions
- [2025-06-11T13:37:00] docs(readme): improve documentation notes and usage guidelines
- [2025-09-09T14:16:42] docs(readme): improve documentation notes and usage guidelines
- [2025-10-29T10:54:40] docs(readme): improve documentation notes and usage guidelines
- [2025-11-06T14:09:59] style: enhance README formatting and badge definitions
- [2025-12-04T20:51:32] docs(readme): improve documentation notes and usage guidelines
- [2026-01-23T11:42:57] docs(readme): improve documentation notes and usage guidelines
