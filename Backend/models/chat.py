from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # Links each chat session to one logged-in user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Simple title shown in the sidebar, like ChatGPT
    title = Column(String(255), nullable=False, default="New Chat")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # One session has many messages
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)

    # Links each message to a chat session
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)

    # Will be either "user" or "assistant"
    role = Column(String(20), nullable=False)

    # Actual message text
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="messages")