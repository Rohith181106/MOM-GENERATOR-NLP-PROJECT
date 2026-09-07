from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    meetings = relationship("Meeting", back_populates="user", cascade="all, delete-orphan")


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, default="Untitled Meeting")
    date = Column(String(50), nullable=True)          # e.g. '2026-09-08'
    start_time = Column(String(50), nullable=True)    # e.g. '10:30 AM'
    duration = Column(Integer, nullable=True, default=0) # Duration in seconds
    meeting_type = Column(String(50), nullable=False, default="LIVE") # LIVE or UPLOAD
    audio_path = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="READY") # LIVE, RECORDING, PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="meetings")
    participants = relationship("Participant", back_populates="meeting", cascade="all, delete-orphan")
    transcript_segments = relationship("TranscriptSegment", back_populates="meeting", cascade="all, delete-orphan")
    topics = relationship("Topic", back_populates="meeting", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="meeting", cascade="all, delete-orphan")
    unresolved_issues = relationship("UnresolvedIssue", back_populates="meeting", cascade="all, delete-orphan")
    mom_document = relationship("MomDocument", back_populates="meeting", uselist=False, cascade="all, delete-orphan")


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    speaker_label = Column(String(50), nullable=True) # e.g. 'SPEAKER_00'
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="participants")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id", ondelete="SET NULL"), nullable=True)
    speaker_label = Column(String(50), nullable=False, default="SPEAKER_00")
    speaker_name = Column(String(255), nullable=True)
    start_time = Column(Float, nullable=False, default=0.0) # seconds
    end_time = Column(Float, nullable=False, default=0.0)   # seconds
    text = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    is_final = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="transcript_segments")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_name = Column(String(255), nullable=False)
    start_time = Column(Float, default=0.0)
    end_time = Column(Float, default=0.0)
    summary = Column(Text, nullable=True)
    embedding_reference = Column(String(255), nullable=True)

    meeting = relationship("Meeting", back_populates="topics")


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    task = Column(Text, nullable=False)
    owner = Column(String(255), nullable=False, default="NEEDS_REVIEW")
    deadline = Column(String(100), nullable=False, default="NEEDS_REVIEW")
    status = Column(String(50), default="PENDING") # PENDING, IN_PROGRESS, COMPLETED
    evidence = Column(Text, nullable=True)
    confidence = Column(Float, default=0.85)
    needs_review = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="action_items")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    decision = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    confidence = Column(Float, default=0.85)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="decisions")


class UnresolvedIssue(Base):
    __tablename__ = "unresolved_issues"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    issue = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="unresolved_issues")


class MomDocument(Base):
    __tablename__ = "mom_documents"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    summary = Column(Text, nullable=False)
    structured_json = Column(JSON, nullable=True) # Full rich structured JSON
    docx_path = Column(String(500), nullable=True)
    pdf_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="mom_document")
