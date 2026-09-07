import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.orm_models import Meeting, MomDocument, User
from backend.app.services.export_service import export_service

router = APIRouter(prefix="/meetings", tags=["Export"])

@router.post("/{meeting_id}/export/docx")
async def export_meeting_docx(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    meeting = await _get_full_meeting_data(meeting_id, current_user, db)
    filename = f"MoM_Meeting_{meeting_id}.docx"
    output_path = os.path.join(settings.EXPORT_DIR, filename)
    export_service.generate_docx(meeting, output_path)

    return FileResponse(
        path=output_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@router.post("/{meeting_id}/export/pdf")
async def export_meeting_pdf(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    meeting = await _get_full_meeting_data(meeting_id, current_user, db)
    filename = f"MoM_Meeting_{meeting_id}.pdf"
    output_path = os.path.join(settings.EXPORT_DIR, filename)
    export_service.generate_pdf(meeting, output_path)

    return FileResponse(
        path=output_path,
        filename=filename,
        media_type="application/pdf"
    )

async def _get_full_meeting_data(meeting_id: int, current_user: User, db: AsyncSession):
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.participants),
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
        raise HTTPException(status_code=404, detail="Meeting not found or unauthorized")

    return {
        "title": meeting.title,
        "date": meeting.date,
        "duration": meeting.duration,
        "meeting_type": meeting.meeting_type,
        "participants": [{"name": p.name} for p in meeting.participants],
        "summary": meeting.mom_document.summary if meeting.mom_document else "No summary generated.",
        "topics": [{"topic_name": t.topic_name, "summary": t.summary} for t in meeting.topics],
        "decisions": [{"decision": d.decision, "evidence": d.evidence} for d in meeting.decisions],
        "action_items": [
            {
                "task": a.task,
                "owner": a.owner,
                "deadline": a.deadline,
                "status": a.status,
                "evidence": a.evidence
            }
            for a in meeting.action_items
        ],
        "unresolved_issues": [{"issue": u.issue} for u in meeting.unresolved_issues]
    }
