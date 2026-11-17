from typing import Optional
from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user, get_optional_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest
from app.schemas.user import UserRegister, UserResponse
from app.services.auth_service import UserService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account",
)
def register(payload: UserRegister):
    service = UserService()
    return service.register(payload)


@router.post(
    "/create-admin",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an Admin account (Bootstrap or Admin-only)",
)
def create_admin(
    payload: UserRegister,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    service = UserService()
    return service.create_admin(payload, current_user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT pair",
)
def login(payload: LoginRequest):
    service = UserService()
    return service.login(payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
def refresh_token(payload: RefreshTokenRequest):
    service = UserService()
    return service.refresh_token(payload.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
