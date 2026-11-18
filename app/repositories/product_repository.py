import uuid
from typing import Optional, List, Tuple
from sqlalchemy import select, update, func
from sqlalchemy.orm import Session
from app.database.session import SessionManager
from app.models.product import Product


class ProductRepository:
    def __init__(self):
        self.db = SessionManager()

    def get_by_id(self, product_id: str | uuid.UUID, session: Optional[Session] = None) -> Optional[Product]:
        if isinstance(product_id, str):
            try:
                product_id = uuid.UUID(product_id)
            except ValueError:
                return None

        if session:
            return session.get(Product, product_id)

        with self.db.session() as s:
            return s.get(Product, product_id)

    def get_by_sku(self, sku: str, session: Optional[Session] = None) -> Optional[Product]:
        stmt = select(Product).where(Product.sku == sku)
        if session:
            return session.execute(stmt).scalar_one_or_none()

        with self.db.session() as s:
            return s.execute(stmt).scalar_one_or_none()

    def get_by_slug(self, slug: str, session: Optional[Session] = None) -> Optional[Product]:
        stmt = select(Product).where(Product.slug == slug)
        if session:
            return session.execute(stmt).scalar_one_or_none()

        with self.db.session() as s:
            return s.execute(stmt).scalar_one_or_none()

    def list_products(
        self,
        category_ids: Optional[List[uuid.UUID]] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        session: Optional[Session] = None,
    ) -> Tuple[List[Product], int]:
        stmt = select(Product)
        count_stmt = select(func.count(Product.id))

        if category_ids is not None and len(category_ids) > 0:
            stmt = stmt.where(Product.category_id.in_(category_ids))
            count_stmt = count_stmt.where(Product.category_id.in_(category_ids))

        if is_active is not None:
            stmt = stmt.where(Product.is_active.is_(is_active))
            count_stmt = count_stmt.where(Product.is_active.is_(is_active))

        if search:
            search_filter = Product.name.ilike(f"%{search}%") | Product.description.ilike(f"%{search}%")
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Product.created_at.desc()).offset(offset).limit(page_size)

        if session:
            total = session.execute(count_stmt).scalar() or 0
            items = list(session.execute(stmt).scalars().all())
            return items, total

        with self.db.session() as s:
            total = s.execute(count_stmt).scalar() or 0
            items = list(s.execute(stmt).scalars().all())
            return items, total

    def create(self, data: dict, session: Optional[Session] = None) -> Product:
        product = Product(**data)
        if session:
            session.add(product)
            session.flush()
            return product

        with self.db.session() as s:
            s.add(product)
            s.commit()
            s.refresh(product)
            return product

    def update(self, product: Product, data: dict, session: Optional[Session] = None) -> Product:
        for key, value in data.items():
            if hasattr(product, key) and value is not None:
                setattr(product, key, value)

        if session:
            session.add(product)
            session.flush()
            return product

        with self.db.session() as s:
            s.add(product)
            s.commit()
            s.refresh(product)
            return product

    def delete(self, product: Product, session: Optional[Session] = None) -> None:
        if session:
            session.delete(product)
            session.flush()
            return

        with self.db.session() as s:
            s.delete(product)
            s.commit()

    def decrement_stock_atomic(self, product_id: uuid.UUID, quantity: int, session: Session) -> bool:
        stmt = (
            update(Product)
            .where(Product.id == product_id, Product.stock >= quantity)
            .values(stock=Product.stock - quantity)
        )
        result = session.execute(stmt)
        return result.rowcount > 0
