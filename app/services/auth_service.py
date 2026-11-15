from app.core.security import hash_password
from app.repositories import UserRepository
from app.schemas.user import UserRegister,UserResponse
from app.core.exceptions import ConflictError


class UserService:

    def __init__(self):
        self.repo = UserRepository()

    def register(self, payload: UserRegister):

        existing = self.repo.get_by_email(payload.email)

        if existing:
            raise ConflictError("Email is already registered.")
        
        

        user = self.repo.create({**payload.model_dump(exclude={"password"}), "password_hash":hash_password(payload.password)})
        user = UserResponse.model_validate(user)
        

        return user