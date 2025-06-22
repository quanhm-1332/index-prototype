import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from db.engines.pg import Base
from ..models import TaskStatus


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        primary_key=True,
    )
    status: Mapped[TaskStatus]
    department: Mapped[str]
    phase: Mapped[str]
    createAt: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updateAt: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
