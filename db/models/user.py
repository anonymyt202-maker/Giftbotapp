from sqlalchemy import BigInteger, String, Integer, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=True)
    stars: Mapped[float] = mapped_column(Float, default=0.0)
    uzs: Mapped[float] = mapped_column(Float, default=0.0)
    referral_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=True)
    referred_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    referral_rewarded: Mapped[bool] = mapped_column(default=False)
    purchases_count: Mapped[int] = mapped_column(Integer, default=0)
    last_daily_bonus: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_slots_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_banned: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user", lazy="select")
