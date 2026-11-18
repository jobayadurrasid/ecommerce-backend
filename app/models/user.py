import uuid
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Boolean, Enum as SQLEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.order import Order


class UserRole(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"


class User(Base):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.CUSTOMER,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user", cascade="all, delete-orphan")
