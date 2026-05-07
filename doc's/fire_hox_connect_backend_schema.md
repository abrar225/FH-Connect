# FireHox Connect — Backend Schema (Database + Auth + Relationships)

## 1. Overview
This schema is designed for a modular, real-time system with clear separation between meeting data, drafts, and users.

Principles:
- Simple, normalized schema
- Clear relationships
- Minimal joins for MVP
- Extendable for future phases

---

## 2. Database: Supabase (PostgreSQL)

---

## 3. Core Tables

### 3.1 users

Stores all platform users

Columns:
- id (uuid, primary key)
- name (text)
- email (text, nullable for MVP)
- created_at (timestamp)

---

### 3.2 meetings

Represents a video session

Columns:
- id (uuid, primary key)
- room_id (text, unique)
- created_by (uuid, fk → users.id)
- started_at (timestamp)
- ended_at (timestamp, nullable)

---

### 3.3 meeting_participants

Mapping users ↔ meetings

Columns:
- id (uuid, primary key)
- meeting_id (uuid, fk → meetings.id)
- user_id (uuid, fk → users.id)
- display_name (text)
- joined_at (timestamp)
- left_at (timestamp, nullable)

Purpose:
- Resolve names like “Rahul” → actual user_id

---

### 3.4 transcripts

Stores transcript chunks

Columns:
- id (uuid, primary key)
- meeting_id (uuid, fk → meetings.id)
- speaker_id (uuid, fk → users.id, nullable)
- speaker_name (text)
- text (text)
- timestamp (timestamp)

---

### 3.5 drafts

Core entity of the system

Columns:
- id (uuid, primary key)
- meeting_id (uuid, fk → meetings.id)
- type (text)  // e.g., "task"
- title (text)
- assignee_id (uuid, fk → users.id, nullable)
- assignee_name (text)
- deadline (timestamp, nullable)
- status (text) // pending | approved | rejected
- confidence (float)
- created_at (timestamp)
- updated_at (timestamp)

---

### 3.6 draft_events

Tracks changes to drafts (optional but useful)

Columns:
- id (uuid, primary key)
- draft_id (uuid, fk → drafts.id)
- event_type (text) // created, updated, approved
- payload (jsonb)
- created_at (timestamp)

---

### 3.7 approved_actions

Final approved outputs

Columns:
- id (uuid, primary key)
- draft_id (uuid, fk → drafts.id)
- meeting_id (uuid)
- action_type (text)
- payload (jsonb)
- executed (boolean default false)
- created_at (timestamp)

---

## 4. Relationships

users (1) → (many) meeting_participants
meetings (1) → (many) meeting_participants

meetings (1) → (many) transcripts
meetings (1) → (many) drafts

users (1) → (many) drafts (assignee)


---

## 5. Auth Flow (Supabase Auth)

### MVP Approach

Simple email-based login OR anonymous session

Flow:
1. User enters name
2. Temporary user created in users table
3. Session stored locally

(No full auth complexity in MVP)

---

## 6. Assignee Resolution Logic

Input:
"Rahul"

Steps:
1. Match with meeting_participants.display_name
2. If match found → assign user_id
3. Else → store as plain text (assignee_name)

---

## 7. Indexing (IMPORTANT)

Add indexes:
- meetings.room_id
- drafts.meeting_id
- transcripts.meeting_id

---

## 8. Constraints

- drafts.status must be enum (pending, approved, rejected)
- meeting_id required for all runtime data

---

## 9. Data Flow Mapping

Transcript → transcripts table
Intent → draft created
Approval → approved_actions

---

## 10. Future Extensions

- organizations table
- roles & permissions
- integration tables (jira, gmail)

---

## 11. Final Definition

This schema supports:
- real-time draft generation
- user mapping
- clean approval workflow

It is intentionally minimal to ensure fast MVP execution.

