from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.orm_models import Meeting, ActionItem, Decision, Topic, User
from backend.app.services.semantic_retrieval import vector_search_service

router = APIRouter(prefix="/meetings", tags=["Search"])

@router.get("/search")
async def search_meetings(
    q: str = Query(..., description="Semantic or keyword search query across meetings"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query_lower = q.lower()

    # 1. Semantic FAISS Vector Search (strictly isolated to user_id)
    vector_results = vector_search_service.search_user_meetings(
        user_id=current_user.id,
        query=q,
        top_k=5
    )

    # 2. Database keyword filtering
    sql_stmt = (
        select(Meeting)
        .options(
            selectinload(Meeting.action_items),
            selectinload(Meeting.decisions),
            selectinload(Meeting.topics)
        )
        .where(Meeting.user_id == current_user.id)
    )
    res = await db.execute(sql_stmt)
    all_user_meetings = res.scalars().all()

    matched_meetings = []
    matched_meeting_ids = set()

    # Add semantic vector hits first
    for v_hit in vector_results:
        m_id = v_hit["meeting_id"]
        matched_meeting_ids.add(m_id)
        # Find meeting object
        m_obj = next((m for m in all_user_meetings if m.id == m_id), None)
        if m_obj:
            matched_meetings.append({
                "id": m_obj.id,
                "title": m_obj.title,
                "date": m_obj.date,
                "match_type": f"Semantic Match ({v_hit['type']})",
                "snippet": v_hit["text"],
                "similarity": v_hit["similarity"]
            })

    # Add SQL text matches
    for m in all_user_meetings:
        if m.id in matched_meeting_ids:
            continue
            
        matched_reason = None
        snippet = None

        if query_lower in m.title.lower():
            matched_reason = "Title Match"
            snippet = m.title
        else:
            # Check actions
            for act in m.action_items:
                if query_lower in act.task.lower() or query_lower in act.owner.lower():
                    matched_reason = f"Action Item ({act.owner})"
                    snippet = act.task
                    break
            # Check decisions
            if not matched_reason:
                for dec in m.decisions:
                    if query_lower in dec.decision.lower():
                        matched_reason = "Decision Match"
                        snippet = dec.decision
                        break
            # Check topics
            if not matched_reason:
                for top in m.topics:
                    if query_lower in top.topic_name.lower():
                        matched_reason = f"Topic ({top.topic_name})"
                        snippet = top.summary
                        break

        if matched_reason:
            matched_meetings.append({
                "id": m.id,
                "title": m.title,
                "date": m.date,
                "match_type": matched_reason,
                "snippet": snippet,
                "similarity": 1.0
            })

    return {
        "query": q,
        "total_results": len(matched_meetings),
        "results": matched_meetings
    }
