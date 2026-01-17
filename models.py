"""
SQLAlchemy ORM Models for Temp Mail Bot
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    """
    Represents a Telegram user who uses the bot.
    """
    __tablename__ = "users"
    
    telegram_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to mails
    mails = relationship("Mail", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class Mail(Base):
    """
    Represents a temporary email created by a user.
    """
    __tablename__ = "mails"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to user
    user = relationship("User", back_populates="mails")
    
    # Index for faster queries on user_id + created_at
    __table_args__ = (
        Index('ix_mails_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        status = "active" if self.is_active else "inactive"
        return f"<Mail(id={self.id}, email={self.email}, status={status})>"

