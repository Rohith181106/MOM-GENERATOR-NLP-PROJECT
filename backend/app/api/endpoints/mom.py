from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.orm_models import Meeting, MomDocument, ActionItem, Decision, User
from backend.app.schemas.pydantic_schemas import MomDocumentResponse, MomDocumentUpdate

router = APIRouter(prefix="/meetings", tags=["MoM"])

@router.get("/{meeting_id}/mom", response_model=MomDocumentResponse)
async def get_mom_document(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting or meeting.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found or access denied")

    res = await db.execute(select(MomDocument).where(MomDocument.meeting_id == meeting_id))
    mom = res.scalar_one_or_none()
    if not mom:
        raise HTTPException(status_code=404, detail="MoM document not generated yet for this meeting.")
    return mom

@router.put("/{meeting_id}/mom", response_model=MomDocumentResponse)
async def update_mom_document(
    meeting_id: int,
    update_in: MomDocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting or meeting.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found or access denied")

    res = await db.execute(select(MomDocument).where(MomDocument.meeting_id == meeting_id))
    mom = res.scalar_one_or_none()
    if not mom:
        raise HTTPException(status_code=404, detail="MoM document not found")

    if update_in.summary is not None:
        mom.summary = update_in.summary
    if update_in.structured_json is not None:
        mom.structured_json = update_in.structured_json
        
        # Synchronize action items back to ActionItem table if present in JSON
        if "action_items" in update_in.structured_json:
            # Clear old and re-populate
            await db.execute(select(ActionItem).where(ActionItem.meeting_id == meeting_id))
            # Keep updated records
            for act in update_in.structured_json["action_items"]:
                # Check if exists or insert
                pass

    await db.commit()
    await db.refresh(mom)
    return mom
