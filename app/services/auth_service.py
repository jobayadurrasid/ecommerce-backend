from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories import UserRepository
from app.schemas.user import UserRegister


class UserService:

    def __init__(self):
        self.repo = UserRepository()

    def register(self, payload: UserRegister):

        existing = self.repo.get_by_email(payload.email)

        if existing:
            raise ValueError("Email is already registered.")

        user = User(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            address=payload.address,
            role=UserRole.CUSTOMER,
            is_active=True,
        )

        return self.repo.create(user)