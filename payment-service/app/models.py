from datetime import datetime
import enum
import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    charged = "charged"
    refunded = "refunded"

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False)
    customer_id = Column(String(64), nullable=False)
    payment_method = Column(String(128), nullable=False)
    idempotency_key = Column(String(128), nullable=False, unique=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending, nullable=False)
    external_txn_id = Column(String(128), nullable=True)
    refunded = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Refund(Base):
    __tablename__ = "refunds"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(36), nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('payment_id', 'idempotency_key', name='uq_payment_refund_idemp'),
    )
