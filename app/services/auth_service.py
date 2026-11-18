from datetime import timedelta
from typing import Optional
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRegister, UserResponse
from app.core.exceptions import ConflictError, UnauthorizedError, NotFoundError, ForbiddenError
from app.models.user import User, UserRole


class UserService:
    def __init__(self):
        self.repo = UserRepository()

    def register(self, payload: UserRegister) -> UserResponse:
        existing = self.repo.get_by_email(payload.email)
        if existing:
            raise ConflictError("Email is already registered.")

        user_data = payload.model_dump(exclude={"password"})
        user_data["password_hash"] = hash_password(payload.password)

        user = self.repo.create(user_data)
        return UserResponse.model_validate(user)

    def create_admin(self, payload: UserRegister, current_user: Optional[User] = None) -> UserResponse:
        admin_count = self.repo.count_admins()
        # If at least one admin exists, require caller to be an admin
        if admin_count > 0:
            if not current_user or current_user.role != UserRole.ADMIN:
                raise ForbiddenError("Admin privileges required to create an admin account.")

        existing = self.repo.get_by_email(payload.email)
        if existing:
            if existing.role == UserRole.ADMIN:
                raise ConflictError("An admin account with this email already exists.")
            # Elevate customer to admin
            with self.repo.db.session() as s:
                user = s.get(User, existing.id)
                user.role = UserRole.ADMIN
                s.commit()
                return UserResponse.model_validate(user)

        user_data = payload.model_dump(exclude={"password"})
        user_data["password_hash"] = hash_password(payload.password)
        user_data["role"] = UserRole.ADMIN

        user = self.repo.create(user_data)
        return UserResponse.model_validate(user)

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.repo.get_by_email(payload.email)
        if not user:
            raise UnauthorizedError("Invalid email or password.")

        if not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")

        if not user.is_active:
            raise UnauthorizedError("Account is inactive.")

        token_data = {"sub": str(user.id), "role": user.role.value, "email": user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def refresh_token(self, refresh_token_str: str) -> TokenResponse:
        payload = decode_token(refresh_token_str)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type for refresh")

        user_id = payload.get("sub")
        user = self.repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User is no longer active or valid")

        token_data = {"sub": str(user.id), "role": user.role.value, "email": user.email}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def get_profile(self, user_id: str) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return UserResponse.model_validate(user)
