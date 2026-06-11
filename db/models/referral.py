from sqlalchemy import Integer, BigInteger, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base
from datetime import datetime


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inviter_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    invited_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    reward_stars: Mapped[float] = mapped_column(Float, default=0)
    rewarded: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
