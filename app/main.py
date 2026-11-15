from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import router
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.exceptions import AppError
app = FastAPI(
    title=settings.APP_NAME,
    description="E-commerce Ordering & Payment System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Router
app.include_router(router)

# Middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": exc.errors(),
        },
    )


# Health Check

@app.get("/", tags=["Root"])
async def root():
    return {
        "application": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy"
    }