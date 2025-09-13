from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .db import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default='driver', nullable=False)
    phone = Column(String, nullable=True)

    reset_token = Column(String, unique=True, nullable=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tickets = relationship("Ticket", back_populates="assigned_user")

class Ticket(Base):
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default='normal')
    status = Column(String, default='open')
    vehicle_id = Column(String, nullable=True)
    telemetry_snapshot = Column(Text, nullable=True)  
    assigned_to = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_user = relationship('User', back_populates="tickets")