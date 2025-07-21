from typing import Any
from sqlalchemy import (  # type: ignore[import]
    Column,
    Integer,
    String,
    ForeignKey,
    Float,
    DateTime,
    Enum,
)
from sqlalchemy.orm import declarative_base, relationship  # type: ignore[import]
from datetime import datetime
import enum

Base: Any = declarative_base()


class TransactionType(enum.Enum):
    deposit = "deposit"
    pix = "pix"
    pix_received = "pix_received"


class User(Base):  # type: ignore[misc]
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    balance = Column(Float, default=0.0)

    transactions = relationship("Transaction", back_populates="user")
    logs = relationship("Log", back_populates="user")


class Transaction(Base):  # type: ignore[misc]
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="transactions")


class Log(Base):  # type: ignore[misc]
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="logs")
