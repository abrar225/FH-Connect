# 🛠️ Installation & Setup Guide

Welcome to **FireHox Connect**! This guide will walk you through setting up the entire project on your local machine. This monorepo includes a **FastAPI backend** and a **Next.js frontend**.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

| Tool | Version | Purpose | Download |
| :--- | :--- | :--- | :--- |
| **Node.js** | 20.x or 24.x | Frontend runtime | [Download](https://nodejs.org/en/download/) |
| **Python** | 3.11.x | Backend runtime | [Download](https://www.python.org/downloads/) |
| **npm** | 10.x+ | Node package manager | (Included with Node.js) |
| **Git** | Optional | Version control | [Download](https://git-scm.com/downloads) |

---

## 🏗️ Step 1: Extract and Initialize

1. **Unzip the Project**: Extract the `FH-Connect.zip` file to a folder of your choice (e.g., `Documents/FH-Connect`).
2. **Open Terminal**: Navigate to the project root:
   ```bash
   cd FH-Connect
   ```

---

## 🐍 Step 2: Backend Setup (Python)

The backend serves the AI logic and WebSocket communication.

1. **Create a Virtual Environment**:
   It's highly recommended to use a virtual environment to keep dependencies isolated.
   ```bash
   cd backend
   python -m venv .venv
   ```

2. **Activate the Environment**:
   - **On Mac/Linux**:
     ```bash
     source .venv/bin/activate
     ```
   - **On Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
   Provide keys for:
   - `GROQ_API_KEY` (Llama models)
   - `GEMINI_API_KEY` (Google models)
   - `DEEPGRAM_API_KEY` (Transcription)
   - `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `DATABASE_URL` (Supabase)
   - `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` (LiveKit)

5. **Run the Backend**:
   ```bash
   python run.py
   ```
   > [!NOTE]
   > The backend should now be running (usually on `http://localhost:8000`).

---

## ⚛️ Step 3: Frontend Setup (Next.js)

The frontend provides the dashboard and user interface.

1. **Navigate and Install**:
   ```bash
   cd ../frontend
   npm install
   ```

2. **Environment Variables**:
   Copy `.env.local.example` to `.env.local`:
   ```bash
   cp .env.local.example .env.local
   ```
   Provide the credentials manually:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_LIVEKIT_URL`

3. **Run the Frontend**:
   ```bash
   npm run dev
   ```
   The application should now be accessible at `http://localhost:3000`.

---

## ☁️ Step 4: External Services Setup

### 🗄️ Supabase (Database & Auth)
1. Create a project at [supabase.com](https://supabase.com).
2. Grab your `Project URL` and `API Key` (anon public) from **Settings > API**.
3. Use the SQL editor to initialize tables or use Prisma (see `prisma-mcp-server` tools if available).

### 🎙️ LiveKit (Media Streaming)
1. Create a project at [livekit.io](https://livekit.io).
2. Copy your Cloud Project URL and generate API keys.

---

## ✅ Step 5: Verification

1. **Verify Backend Connection**:
   Open a browser and navigate to `http://localhost:8000/docs`. You should see the FastAPI Swagger UI.
2. **Verify Frontend UI**:
   Navigate to `http://localhost:3000`. Sign in with Supabase and start a new meeting.
3. **Verify AI Transcription**:
   Join a meeting, enable your microphone, and check if transcription appears in the meeting pulse.

---

## 💡 Troubleshooting

- **Python Version**: If `python -m venv` fails, try `python3.11 -m venv`.
- **Node Dependencies**: If `npm install` errors, try `npm install --legacy-peer-deps`.
- **WebSocket Issues**: Ensure the backend is running *before* starting a session on the frontend.
- **Port Conflicts**: If port `:3000` is busy, Next.js will use `:3001`. Ensure your `LIVEKIT_URL` matches the frontend configuration.

---

Made by the FireHox Team. For further assistance, contact the development lead.
