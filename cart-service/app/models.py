from datetime import datetime
import uuid

from sqlalchemy import Column, String, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(64), nullable=False)
    product_id = Column(String(36), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    price_cents = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('customer_id', 'product_id', name='uq_customer_product'),
    )
