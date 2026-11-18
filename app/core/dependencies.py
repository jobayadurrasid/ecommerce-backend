from typing import Callable, Optional
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
) -> User:
    if not credentials or not credentials.credentials:
        raise UnauthorizedError("Missing authentication token")

    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    user_repo = UserRepository()
    user = user_repo.get_by_id(user_id)

    if not user:
        raise UnauthorizedError("User no longer exists")

    if not user.is_active:
        raise ForbiddenError("User account is inactive")

    return user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Optional[User]:
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        return UserRepository().get_by_id(user_id)
    except Exception:
        return None


def require_role(required_role: UserRole) -> Callable:
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise ForbiddenError(f"Access denied: {required_role.value} privileges required")
        return current_user

    return role_checker


require_admin = require_role(UserRole.ADMIN)
