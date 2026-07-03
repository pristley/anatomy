from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from database.base import Base
from datetime import datetime


class Agent(Base):
    __tablename__ = 'agents'
    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    model = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    config = Column(Text, nullable=True)
    owner_id = Column(String(36), nullable=True)
    status = Column(String(50), default='idle')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    archived = Column(Boolean, default=False)
    stats = Column(Text, nullable=True)
    messages = relationship('Message', back_populates='agent', cascade='all, delete-orphan')


class Message(Base):
    __tablename__ = 'messages'
    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey('agents.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    payload = Column(Text)
    agent = relationship('Agent', back_populates='messages')
