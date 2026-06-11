from sqlalchemy import BigInteger, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base
from datetime import datetime


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    gift_id: Mapped[int] = mapped_column(Integer, ForeignKey("gifts.id"))
    target_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    target_username: Mapped[str] = mapped_column(String(64), nullable=True)
    amount_stars: Mapped[float] = mapped_column(Float)
    amount_uzs: Mapped[float] = mapped_column(Float, default=0)
    pay_with: Mapped[str] = mapped_column(String(16), default="stars")  # stars | uzs
    anonymous: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | success | failed
    error_msg: Mapped[str] = mapped_column(Text, nullable=True)
    promo_code: Mapped[str] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="orders")
    gift: Mapped["Gift"] = relationship("Gift", back_populates="orders")
