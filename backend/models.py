from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship
import time

try:
    from database import Base
except ImportError:
    from backend.database import Base

class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    auth_token = Column(String(255), index=True, nullable=True)
    created_at = Column(String(50), default=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    last_login = Column(String(50), default=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))

    sessions = relationship("ChatSessionModel", back_populates="owner", cascade="all, delete-orphan")


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    title = Column(String(255), default="New Conversation")
    created_at = Column(String(50), default=lambda: time.strftime("%b %d, %I:%M %p"))
    updated_at = Column(String(50), default=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))

    owner = relationship("UserModel", back_populates="sessions")
    messages = relationship("ChatMessageModel", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessageModel.id")


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    session_id = Column(String(50), ForeignKey("chat_sessions.session_id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    image_data = Column(Text, nullable=True)
    created_at = Column(String(50), default=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))

    session = relationship("ChatSessionModel", back_populates="messages")
