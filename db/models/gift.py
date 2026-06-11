from sqlalchemy import String, Integer, Float, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base
from datetime import datetime


class Gift(Base):
    __tablename__ = "gifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price_stars: Mapped[int] = mapped_column(Integer)           # Stars narxi
    tg_gift_id: Mapped[str] = mapped_column(String(64))         # Telegram Gift ID
    sticker_url: Mapped[str] = mapped_column(String(512), nullable=True)
    image_url: Mapped[str] = mapped_column(String(512), nullable=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=True)
    category: Mapped[str] = mapped_column(String(64), default="Umumiy")
    stock: Mapped[int] = mapped_column(Integer, default=-1)     # -1 = cheksiz
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="gift", lazy="select")
