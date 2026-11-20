import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import SessionManager
from app.models.payment import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self):
        self.db = SessionManager()

    def get_by_id(self, payment_id: str | uuid.UUID, session: Optional[Session] = None) -> Optional[Payment]:
        if isinstance(payment_id, str):
            try:
                payment_id = uuid.UUID(payment_id)
            except ValueError:
                return None

        if session:
            return session.get(Payment, payment_id)

        with self.db.session() as s:
            return s.get(Payment, payment_id)

    def get_by_idempotency_key(self, key: str, session: Optional[Session] = None) -> Optional[Payment]:
        stmt = select(Payment).where(Payment.idempotency_key == key)
        if session:
            return session.execute(stmt).scalar_one_or_none()

        with self.db.session() as s:
            return s.execute(stmt).scalar_one_or_none()

    def get_by_transaction_id(self, tx_id: str, session: Optional[Session] = None) -> Optional[Payment]:
        stmt = select(Payment).where(Payment.transaction_id == tx_id)
        if session:
            return session.execute(stmt).scalar_one_or_none()

        with self.db.session() as s:
            return s.execute(stmt).scalar_one_or_none()

    def create(self, data: dict, session: Optional[Session] = None) -> Payment:
        payment = Payment(**data)
        if session:
            session.add(payment)
            session.flush()
            return payment

        with self.db.session() as s:
            s.add(payment)
            s.commit()
            s.refresh(payment)
            return payment

    def update_status(
        self,
        payment: Payment,
        status: PaymentStatus,
        transaction_id: Optional[str] = None,
        gateway_response: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> Payment:
        payment.status = status
        if transaction_id:
            payment.transaction_id = transaction_id
        if gateway_response:
            payment.gateway_response = gateway_response

        if session:
            session.add(payment)
            session.flush()
            return payment

        with self.db.session() as s:
            s.add(payment)
            s.commit()
            s.refresh(payment)
            return payment
