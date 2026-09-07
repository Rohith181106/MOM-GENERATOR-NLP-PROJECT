# Automated Minutes of Meeting (MoM) Generator

A complete, production-grade AI-powered full-stack application that transforms multi-speaker meetings (both live sessions and uploaded recordings) into structured, evidence-grounded Minutes of Meeting (MoM).

---

## ?? Key Highlights & Architecture

Unlike generic one-shot LLM wrappers, this system implements a **multi-stage, task-specific NLP/ML pipeline**:

```
Meeting Audio (Live / Upload)
             ?
Speech-to-Text (faster-whisper)
             ?
Speaker Diarization (pyannote.audio)
             ?
Transcript + Speaker Alignment & Roster Mapping
             ?
Action Item Detection (DeBERTa-v3)
             ?
Decision & Dialogue Act Classification (DeBERTa-v3)
             ?
Owner & Normalized Deadline Resolution (dateparser)
             ?
Semantic Topic Segmentation (all-MiniLM-L6-v2)
             ?
Evidence Retrieval & Vector Storage (FAISS)
             ?
MoM Synthesis & Zero-Hallucination Grounding (Qwen-2.5-3B)
             ?
Editable MoM Workspace & Document Export (DOCX / PDF / JSON)
             ?
Persistent User Memory (PostgreSQL / SQLite fallback)
```

---

## ?? Features

1. **Authentication & Strict User Isolation**
   - JWT tokens, bcrypt password hashing.
   - Every meeting and semantic vector record is strictly scoped to the authenticated user ID (`user_id == current_user.id`).

2. **ChatGPT-like Persistent Meeting Memory**
   - Left navigation drawer organizing meetings into Recent and Older.
   - All meetings, transcripts, decisions, and action items persist permanently across browser restarts and logouts.

3. **Live Meetings with Real-Time Transcription**
   - Conduct live meetings directly in the app.
   - Microphones stream audio over WebSockets (`/ws/meetings/{id}`).
   - Instant visual distinction between **Interim** (in-flight speech) and **Final** transcript segments.
   - Real-time preliminary **Action Item** and **Decision** detection popups during the meeting.

4. **Upload Previous Meeting Recordings**
   - Ingests MP3, WAV, M4A, MP4, and WebM files up to 500MB.
   - Visual 9-stage pipeline tracker showing ASR, Diarization, Action detection, Decision detection, Topic segmentation, and MoM Generation.

5. **Evidence-Grounded Action Items & Decisions**
   - Strict zero-fabrication: every action item and decision cites exact quote evidence from the transcript.
   - Ambiguities are marked with `NEEDS_REVIEW`.
   - Natural language deadlines ("Friday", "next Monday", "tomorrow") normalized to standard `YYYY-MM-DD`.

6. **Interactive MoM Editor & Document Export**
   - Editable Executive Summary, Topics, Key Decisions, Action Items (Task, Owner, Deadline, Status).
   - One-click export to formatted **DOCX** (`python-docx`) and styled **PDF** (`ReportLab`).

7. **Semantic Memory Search**
   - Vector similarity search powered by FAISS + `all-MiniLM-L6-v2` embeddings alongside SQL text filters.
   - Example queries: *"Show my meetings about API"*, *"Find decisions related to database"*.

---

## ?? Tech Stack

- **Backend**: FastAPI (Python 3.10+), SQLAlchemy 2.0 (PostgreSQL primary with seamless SQLite fallback), WebSockets, faster-whisper, pyannote.audio, DeBERTa-v3, python-docx, ReportLab.
- **Frontend**: React 18, Vite, Tailwind CSS, Three.js 3D Canvas, Lucide Icons, Axios.
- **Testing**: pytest, pytest-asyncio, httpx.

---

## ?? Running the Application

### 1. Start the Backend
```powershell
.\run_backend.ps1
# Or manually:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at: `http://localhost:8000/docs`

### 2. Start the Frontend
```powershell
.\run_frontend.ps1
# Or manually:
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser!

### 3. Run Automated Tests
```powershell
python -m pytest backend/tests/test_api.py -v
```
