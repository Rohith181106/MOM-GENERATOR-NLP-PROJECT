from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.orm_models import Meeting, TranscriptSegment, User
from backend.app.schemas.pydantic_schemas import TranscriptSegmentResponse

router = APIRouter(prefix="/meetings", tags=["Transcript"])

@router.get("/{meeting_id}/transcript", response_model=List[TranscriptSegmentResponse])
async def get_transcript(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting or meeting.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found or access denied")

    res = await db.execute(
        select(TranscriptSegment)
        .where(TranscriptSegment.meeting_id == meeting_id)
        .order_by(TranscriptSegment.start_time.asc())
    )
    segments = res.scalars().all()
    return segments
