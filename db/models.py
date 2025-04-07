import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at = Column(DateTime, default=datetime.now(timezone.utc))
    messages = relationship("Message", back_populates="conversation")
    prompt_profile_id = Column(UUID(as_uuid=True), ForeignKey("prompt_profiles.id"), nullable=True)
    prompt_profile = relationship("PromptProfile")
    knowledge_sources = relationship("KnowledgeSource", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    thumbs_up = Column(Boolean, nullable=True)
    thumbs_down = Column(Boolean, nullable=True)
    feedback_text = Column(Text, nullable=True)
    conversation = relationship("Conversation", back_populates="messages")

class PromptProfile(Base):
    __tablename__ = "prompt_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True)
    system_prompt = Column(Text)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    content = Column(Text)
    added_at = Column(DateTime, default=datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="knowledge_sources")
