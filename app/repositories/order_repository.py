import uuid
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from app.database.session import SessionManager
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem


class OrderRepository:
    def __init__(self):
        self.db = SessionManager()

    def get_by_id(self, order_id: str | uuid.UUID, session: Optional[Session] = None) -> Optional[Order]:
        if isinstance(order_id, str):
            try:
                order_id = uuid.UUID(order_id)
            except ValueError:
                return None

        stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        if session:
            return session.execute(stmt).scalar_one_or_none()

        with self.db.session() as s:
            return s.execute(stmt).scalar_one_or_none()

    def get_by_order_number(self, order_number: str, session: Optional[Session] = None) -> Optional[Order]:
        stmt = select(Order).options(selectinload(Order.items)).where(Order.order_number == order_number)
        if session:
            return session.execute(stmt).scalar_one_or_none()

        with self.db.session() as s:
            return s.execute(stmt).scalar_one_or_none()

    def create(
        self,
        order_data: dict,
        items_data: List[dict],
        session: Optional[Session] = None,
    ) -> Order:
        order = Order(**order_data)

        if session:
            session.add(order)
            session.flush()
            for item_data in items_data:
                item = OrderItem(order_id=order.id, **item_data)
                session.add(item)
            session.flush()
            stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
            return session.execute(stmt).scalar_one()

        with self.db.session() as s:
            s.add(order)
            s.flush()
            for item_data in items_data:
                item = OrderItem(order_id=order.id, **item_data)
                s.add(item)
            s.commit()
            stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
            return s.execute(stmt).scalar_one()

    def list_by_user(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        session: Optional[Session] = None,
    ) -> Tuple[List[Order], int]:
        stmt = select(Order).options(selectinload(Order.items)).where(Order.user_id == user_id)
        count_stmt = select(func.count(Order.id)).where(Order.user_id == user_id)

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(page_size)

        if session:
            total = session.execute(count_stmt).scalar() or 0
            orders = list(session.execute(stmt).scalars().all())
            return orders, total

        with self.db.session() as s:
            total = s.execute(count_stmt).scalar() or 0
            orders = list(s.execute(stmt).scalars().all())
            return orders, total

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        session: Optional[Session] = None,
    ) -> Tuple[List[Order], int]:
        stmt = select(Order).options(selectinload(Order.items))
        count_stmt = select(func.count(Order.id))

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(page_size)

        if session:
            total = session.execute(count_stmt).scalar() or 0
            orders = list(session.execute(stmt).scalars().all())
            return orders, total

        with self.db.session() as s:
            total = s.execute(count_stmt).scalar() or 0
            orders = list(s.execute(stmt).scalars().all())
            return orders, total

    def update_status(self, order: Order, status: OrderStatus, session: Optional[Session] = None) -> Order:
        if session:
            order.status = status
            session.add(order)
            session.flush()
            stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
            return session.execute(stmt).scalar_one()

        with self.db.session() as s:
            order_in_db = s.get(Order, order.id)
            order_in_db.status = status
            s.add(order_in_db)
            s.commit()
            stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
            return s.execute(stmt).scalar_one()
