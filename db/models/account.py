from sqlalchemy import Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base
from datetime import datetime


class TgAccount(Base):
    __tablename__ = "tg_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(32), unique=True)
    session_string: Mapped[str] = mapped_column(Text, nullable=True)   # StringSession
    username: Mapped[str] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=True)
    tg_id: Mapped[int] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    stars_balance: Mapped[int] = mapped_column(Integer, default=0)
    gifts_sent: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used: Mapped[datetime] = mapped_column(DateTime, nullable=True)
