from sqlalchemy import select
from app.database.session import SessionManager
from app.models.user import User


class UserRepository:

    def __init__(self):
        self.db = SessionManager()

    def get_by_email(self, email):
        with self.db.session() as session:
            result = session.execute(
                select(User).where(User.email == email)
            ).scalar_one_or_none()

        return result

    def create(self, data):
        user = User(**data)
        with self.db.session() as session:
            session.add(user)
            session.commit()
            session.refresh(user)

        return user