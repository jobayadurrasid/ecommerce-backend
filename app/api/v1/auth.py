from fastapi import APIRouter, Depends, status
from app.schemas.user import UserRegister, UserResponse
from app.services import UserService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register( payload: UserRegister):
    service = UserService()

    return service.register(payload)


@router.post("/login")
def login():
    return {"message": "Login"}