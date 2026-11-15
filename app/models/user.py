import uuid
from enum import Enum
from typing import Optional
from sqlalchemy import Boolean, Enum as SQLEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"



class User(Base):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(String(255))

    address: Mapped[Optional[str]] = mapped_column(String(255))

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.CUSTOMER,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
    )


