import os
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.orm_models import (
    User, Meeting, Participant, TranscriptSegment, Topic,
    ActionItem, Decision, UnresolvedIssue, MomDocument
)
from backend.app.schemas.pydantic_schemas import (
    MeetingCreate, MeetingResponse, MeetingDetailResponse
)
from backend.app.services.speech_to_text import stt_service
from backend.app.services.diarization import diarization_service
from backend.app.services.alignment import aligner_service
from backend.app.services.action_detector import action_detector
from backend.app.services.decision_detector import decision_detector
from backend.app.services.owner_deadline_resolver import resolver_service
from backend.app.services.topic_segmenter import topic_segmenter
from backend.app.services.mom_generator import mom_generator_service
from backend.app.services.semantic_retrieval import vector_search_service

router = APIRouter(prefix="/meetings", tags=["Meetings"])

@router.get("", response_model=List[MeetingResponse])
async def list_user_meetings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Strictly isolated to authenticated user
    result = await db.execute(
        select(Meeting).where(Meeting.user_id == current_user.id).order_by(Meeting.created_at.desc())
    )
    meetings = result.scalars().all()
    return meetings

@router.post("", response_model=MeetingDetailResponse)
async def create_meeting(
    meeting_in: MeetingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    now = datetime.utcnow()
    meeting = Meeting(
        user_id=current_user.id,
        title=meeting_in.title,
        date=meeting_in.date or now.strftime("%Y-%m-%d"),
        start_time=meeting_in.start_time or now.strftime("%I:%M %p"),
        meeting_type=meeting_in.meeting_type or "LIVE",
        status="READY"
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    # Add participants
    roster = meeting_in.participants or ["Rohith", "Dharun", "Priya"]
    for i, name in enumerate(roster):
        p = Participant(
            meeting_id=meeting.id,
            name=name,
            speaker_label=f"SPEAKER_{i:02d}"
        )
        db.add(p)
    await db.commit()

    # Re-fetch with relationships
    return await get_meeting_by_id(meeting.id, current_user, db)

@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
async def get_meeting_by_id(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.participants),
            selectinload(Meeting.transcript_segments),
            selectinload(Meeting.topics),
            selectinload(Meeting.action_items),
            selectinload(Meeting.decisions),
            selectinload(Meeting.unresolved_issues),
            selectinload(Meeting.mom_document)
        )
        .where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    # Crucial security validation: prevent cross-user access
    if meeting.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied: You cannot access another user's meeting.")
        
    return meeting

@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(meeting)
    await db.commit()
    return {"message": "Meeting deleted successfully"}

@router.post("/upload", response_model=MeetingDetailResponse)
async def upload_meeting_file(
    title: str = Form("Uploaded Meeting"),
    date: Optional[str] = Form(None),
    participants: Optional[str] = Form("Rohith, Dharun, Priya"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = [".mp3", ".wav", ".m4a", ".mp4", ".webm"]
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format {ext}. Allowed: {', '.join(allowed_exts)}"
        )

    now = datetime.utcnow()
    meeting = Meeting(
        user_id=current_user.id,
        title=title,
        date=date or now.strftime("%Y-%m-%d"),
        start_time=now.strftime("%I:%M %p"),
        meeting_type="UPLOAD",
        status="PROCESSING"
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    # Save uploaded file
    file_path = os.path.join(settings.UPLOAD_DIR, f"meeting_{meeting.id}{ext}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    meeting.audio_path = file_path
    await db.commit()

    # Create participants
    roster = [p.strip() for p in participants.split(",") if p.strip()]
    for i, name in enumerate(roster):
        db.add(Participant(
            meeting_id=meeting.id,
            name=name,
            speaker_label=f"SPEAKER_{i:02d}"
        ))
    await db.commit()

    # Automatically process uploaded meeting
    return await execute_full_pipeline(meeting.id, current_user, db)

@router.post("/{meeting_id}/start")
async def start_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting or meeting.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting.status = "LIVE"
    await db.commit()
    return {"status": "LIVE"}

@router.post("/{meeting_id}/end")
async def end_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting or meeting.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    meeting.status = "PROCESSING"
    await db.commit()

    # Run post-meeting complete processing pipeline
    return await execute_full_pipeline(meeting_id, current_user, db)

@router.post("/{meeting_id}/process", response_model=MeetingDetailResponse)
async def process_meeting_endpoint(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await execute_full_pipeline(meeting_id, current_user, db)

async def execute_full_pipeline(meeting_id: int, current_user: User, db: AsyncSession):
    """
    Executes the complete 9-stage NLP/ML pipeline:
    1. ASR (Speech-to-Text)
    2. Speaker Diarization
    3. Transcript + Speaker Alignment
    4. Action Item Detection
    5. Decision & Unresolved Detection
    6. Owner & Deadline Resolution
    7. Topic Segmentation
    8. MoM Generation & Evidence Grounding
    9. PostgreSQL Storage & FAISS Vector Indexing
    """
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.participants),
            selectinload(Meeting.transcript_segments),
            selectinload(Meeting.topics),
            selectinload(Meeting.action_items),
            selectinload(Meeting.decisions),
            selectinload(Meeting.unresolved_issues),
            selectinload(Meeting.mom_document)
        )
        .where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    if not meeting or meeting.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")

    roster = [p.name for p in meeting.participants] or ["Rohith", "Dharun", "Priya"]

    # 1. Transcript Acquisition
    if not meeting.transcript_segments:
        # If uploaded audio or empty live meeting, perform ASR
        raw_segments = stt_service.transcribe_audio_file(meeting.audio_path or "")
        # Diarize
        diar_intervals = diarization_service.diarize_audio(meeting.audio_path or "")
        # Align
        aligned = aligner_service.align(raw_segments, diar_intervals, roster)
        for seg in aligned:
            s_obj = TranscriptSegment(
                meeting_id=meeting.id,
                speaker_label=seg["speaker_label"],
                speaker_name=seg["speaker_name"],
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                text=seg["text"],
                confidence=seg.get("confidence", 0.96),
                is_final=True
            )
            meeting.transcript_segments.append(s_obj)
        await db.commit()

    segments = meeting.transcript_segments
    seg_dicts = [
        {"start_time": s.start_time, "end_time": s.end_time, "text": s.text, "speaker_name": s.speaker_name or s.speaker_label}
        for s in segments
    ]

    # 2. Action Items
    raw_actions = action_detector.extract_actions_from_segments(seg_dicts)
    for act in raw_actions:
        # Resolve owner and deadline
        resolved_owner = resolver_service.resolve_owner(act["owner"], speaker_name=act.get("speaker_name"), roster=roster)
        resolved_deadline = resolver_service.resolve_deadline(act["deadline"], base_date_str=meeting.date)
        
        a_obj = ActionItem(
            meeting_id=meeting.id,
            task=act["task"],
            owner=resolved_owner,
            deadline=resolved_deadline,
            status="PENDING",
            evidence=act.get("evidence"),
            confidence=act.get("confidence", 0.94),
            needs_review=(resolved_owner == "NEEDS_REVIEW" or resolved_deadline == "NEEDS_REVIEW")
        )
        meeting.action_items.append(a_obj)

    # 3. Decisions & Unresolved
    dec_unres = decision_detector.extract_decisions_and_issues(seg_dicts)
    for dec in dec_unres["decisions"]:
        meeting.decisions.append(Decision(
            meeting_id=meeting.id,
            decision=dec["decision"],
            evidence=dec["evidence"],
            confidence=dec.get("confidence", 0.95)
        ))
    for unres in dec_unres["unresolved_issues"]:
        meeting.unresolved_issues.append(UnresolvedIssue(
            meeting_id=meeting.id,
            issue=unres["issue"],
            evidence=unres["evidence"]
        ))

    # 4. Topic Segmentation
    segmented_topics = topic_segmenter.segment_topics(seg_dicts)
    for top in segmented_topics:
        meeting.topics.append(Topic(
            meeting_id=meeting.id,
            topic_name=top["topic_name"],
            start_time=top["start_time"],
            end_time=top["end_time"],
            summary=top["summary"]
        ))
    await db.commit()

    # 5. MoM Generation
    mom_result = mom_generator_service.generate_mom(
        meeting_title=meeting.title,
        date_str=meeting.date or datetime.utcnow().strftime("%Y-%m-%d"),
        participants=roster,
        segments=seg_dicts,
        topics=segmented_topics,
        actions=raw_actions,
        decisions=dec_unres["decisions"],
        unresolved=dec_unres["unresolved_issues"]
    )

    mom_doc = MomDocument(
        meeting_id=meeting.id,
        summary=mom_result["summary"],
        structured_json=mom_result["structured_json"]
    )
    meeting.mom_document = mom_doc

    # Calculate duration
    if segments:
        meeting.duration = int(segments[-1].end_time - segments[0].start_time)
    meeting.status = "COMPLETED"
    await db.commit()

    # 6. FAISS Vector Indexing for isolated persistent memory
    action_texts = [a["task"] for a in raw_actions]
    decision_texts = [d["decision"] for d in dec_unres["decisions"]]
    vector_search_service.index_meeting(
        user_id=current_user.id,
        meeting_id=meeting.id,
        title=meeting.title,
        summary=mom_result["summary"],
        action_items=action_texts,
        decisions=decision_texts
    )

    return meeting
