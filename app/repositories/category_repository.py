import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.database.session import SessionManager
from app.models.category import Category


class CategoryRepository:
    def __init__(self):
        self.db = SessionManager()

    def get_by_id(self, category_id: str | uuid.UUID, session: Optional[Session] = None) -> Optional[Category]:
        if isinstance(category_id, str):
            try:
                category_id = uuid.UUID(category_id)
            except ValueError:
                return None

        stmt = select(Category).options(selectinload(Category.children)).where(Category.id == category_id)
        if session:
            return session.execute(stmt).scalar_one_or_none()

        with self.db.session() as s:
            return s.execute(stmt).scalar_one_or_none()

    def get_by_slug(self, slug: str, session: Optional[Session] = None) -> Optional[Category]:
        stmt = select(Category).where(Category.slug == slug)
        if session:
            return session.execute(stmt).scalar_one_or_none()

        with self.db.session() as s:
            return s.execute(stmt).scalar_one_or_none()

    def get_all(self, active_only: bool = True, session: Optional[Session] = None) -> List[Category]:
        stmt = select(Category).options(selectinload(Category.children))
        if active_only:
            stmt = stmt.where(Category.is_active.is_(True))
        stmt = stmt.order_by(Category.name.asc())

        if session:
            return list(session.execute(stmt).scalars().all())

        with self.db.session() as s:
            return list(s.execute(stmt).scalars().all())

    def get_root_categories(self, active_only: bool = True, session: Optional[Session] = None) -> List[Category]:
        stmt = select(Category).options(selectinload(Category.children)).where(Category.parent_id.is_(None))
        if active_only:
            stmt = stmt.where(Category.is_active.is_(True))
        stmt = stmt.order_by(Category.name.asc())

        if session:
            return list(session.execute(stmt).scalars().all())

        with self.db.session() as s:
            return list(s.execute(stmt).scalars().all())

    def create(self, data: dict, session: Optional[Session] = None) -> Category:
        category = Category(**data)
        if session:
            session.add(category)
            session.flush()
            return category

        with self.db.session() as s:
            s.add(category)
            s.commit()
            s.refresh(category)
            return category

    def update(self, category: Category, data: dict, session: Optional[Session] = None) -> Category:
        for key, value in data.items():
            if hasattr(category, key):
                setattr(category, key, value)

        if session:
            session.add(category)
            session.flush()
            return category

        with self.db.session() as s:
            s.add(category)
            s.commit()
            s.refresh(category)
            return category

    def delete(self, category: Category, session: Optional[Session] = None) -> None:
        if session:
            session.delete(category)
            session.flush()
            return

        with self.db.session() as s:
            s.delete(category)
            s.commit()
