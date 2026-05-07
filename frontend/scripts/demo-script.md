# FireHox Connect — Demo Validation Script

Use this script during live demonstrations or final performance testing to guarantee clean transcription and perfectly extracted tasks. These phrases are designed to trigger high-confidence detections by the AI task extraction pipeline.

### Preparation
1. Ensure the frontend and backend are running locally (`npm run dev` and `uvicorn app.main:app`).
2. Start the LiveKit server.
3. Open the meeting room in Chrome (gives best Web Speech API performance).
4. Un-mute the microphone.

---

### Test Phrase 1: Standard Assignment
**Speak clearly:**
> "Alright team, Rahul you need to finish the login page UI by tomorrow morning so we don't block the backend."

**Expected Output (Sidebar Draft):**
- **Title:** Finish login page UI
- **Assignee:** Rahul
- **Deadline:** Tomorrow morning

---

### Test Phrase 2: Status Update + Action Item
**Speak clearly:**
> "I reviewed the API docs, they look good. Sarah, please review the PR for the checkout flow by Friday."

**Expected Output (Sidebar Draft):**
- **Title:** Review the PR for the checkout flow
- **Assignee:** Sarah
- **Deadline:** Friday

---

### Test Phrase 3: Self-Assignment
**Speak clearly:**
> "That's a good point. I will fix the header alignment issue by end of day today."

**Expected Output (Sidebar Draft):**
- **Title:** Fix the header alignment issue
- **Assignee:** I (or current user name if context aware)
- **Deadline:** End of day today

---

### Test Phrase 4: Complex Multi-part sentence
**Speak clearly:**
> "Since the database migration is taking longer than expected, John, could you write a quick rollback script by Thursday evening just in case?"

**Expected Output (Sidebar Draft):**
- **Title:** Write a quick rollback script
- **Assignee:** John
- **Deadline:** Thursday evening

---

### Test Phrase 5: Vague Deadline
**Speak clearly:**
> "We also need someone to update the readme file with the new environment variables soon."

**Expected Output (Sidebar Draft):**
- **Title:** Update the readme file with the new environment variables
- **Assignee:** Unassigned
- **Deadline:** Soon / Unspecified
