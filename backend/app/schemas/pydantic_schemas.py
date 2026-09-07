from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr

# Auth Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[str] = None

# Participant Schemas
class ParticipantCreate(BaseModel):
    name: str
    speaker_label: Optional[str] = None
    email: Optional[str] = None

class ParticipantResponse(BaseModel):
    id: int
    name: str
    speaker_label: Optional[str] = None
    email: Optional[str] = None
    class Config:
        from_attributes = True

# Transcript Segment Schemas
class TranscriptSegmentCreate(BaseModel):
    speaker_label: str
    speaker_name: Optional[str] = None
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float] = 1.0
    is_final: Optional[bool] = True

class TranscriptSegmentResponse(BaseModel):
    id: int
    meeting_id: int
    speaker_label: str
    speaker_name: Optional[str] = None
    start_time: float
    end_time: float
    text: str
    confidence: float
    is_final: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Topic Schemas
class TopicResponse(BaseModel):
    id: int
    meeting_id: int
    topic_name: str
    start_time: float
    end_time: float
    summary: Optional[str] = None
    class Config:
        from_attributes = True

# Action Item Schemas
class ActionItemCreate(BaseModel):
    task: str
    owner: Optional[str] = "NEEDS_REVIEW"
    deadline: Optional[str] = "NEEDS_REVIEW"
    status: Optional[str] = "PENDING"
    evidence: Optional[str] = None
    confidence: Optional[float] = 0.85
    needs_review: Optional[bool] = False

class ActionItemUpdate(BaseModel):
    task: Optional[str] = None
    owner: Optional[str] = None
    deadline: Optional[str] = None
    status: Optional[str] = None
    needs_review: Optional[bool] = None

class ActionItemResponse(BaseModel):
    id: int
    meeting_id: int
    task: str
    owner: str
    deadline: str
    status: str
    evidence: Optional[str] = None
    confidence: float
    needs_review: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Decision Schemas
class DecisionResponse(BaseModel):
    id: int
    meeting_id: int
    decision: str
    evidence: Optional[str] = None
    confidence: float
    created_at: datetime
    class Config:
        from_attributes = True

# Unresolved Issue Schemas
class UnresolvedIssueResponse(BaseModel):
    id: int
    meeting_id: int
    issue: str
    evidence: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# MoM Document Schemas
class MomDocumentUpdate(BaseModel):
    summary: Optional[str] = None
    structured_json: Optional[Dict[str, Any]] = None

class MomDocumentResponse(BaseModel):
    id: int
    meeting_id: int
    summary: str
    structured_json: Optional[Dict[str, Any]] = None
    docx_path: Optional[str] = None
    pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Meeting Schemas
class MeetingCreate(BaseModel):
    title: str = "Project Discussion"
    date: Optional[str] = None
    start_time: Optional[str] = None
    meeting_type: Optional[str] = "LIVE"
    participants: Optional[List[str]] = []

class MeetingResponse(BaseModel):
    id: int
    user_id: int
    title: str
    date: Optional[str] = None
    start_time: Optional[str] = None
    duration: Optional[int] = 0
    meeting_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class MeetingDetailResponse(MeetingResponse):
    participants: List[ParticipantResponse] = []
    transcript_segments: List[TranscriptSegmentResponse] = []
    topics: List[TopicResponse] = []
    action_items: List[ActionItemResponse] = []
    decisions: List[DecisionResponse] = []
    unresolved_issues: List[UnresolvedIssueResponse] = []
    mom_document: Optional[MomDocumentResponse] = None

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 10
