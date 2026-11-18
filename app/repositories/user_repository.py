import uuid
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.database.session import SessionManager
from app.models.user import User, UserRole


class UserRepository:
    def __init__(self):
        self.db = SessionManager()

    def get_by_id(self, user_id: str | uuid.UUID, session: Optional[Session] = None) -> Optional[User]:
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return None

        if session:
            return session.get(User, user_id)

        with self.db.session() as s:
            return s.get(User, user_id)

    def get_by_email(self, email: str, session: Optional[Session] = None) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        if session:
            return session.execute(stmt).scalar_one_or_none()

        with self.db.session() as s:
            return s.execute(stmt).scalar_one_or_none()

    def count_admins(self, session: Optional[Session] = None) -> int:
        stmt = select(func.count(User.id)).where(User.role == UserRole.ADMIN)
        if session:
            return session.execute(stmt).scalar() or 0

        with self.db.session() as s:
            return s.execute(stmt).scalar() or 0

    def create(self, data: dict, session: Optional[Session] = None) -> User:
        user = User(**data)
        if session:
            session.add(user)
            session.flush()
            return user

        with self.db.session() as s:
            s.add(user)
            s.commit()
            s.refresh(user)
            return user
