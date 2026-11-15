
class AppError(Exception):
    def __init__(
        self,
        message: str = "Something went wrong",
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: dict | list | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message="Resource not found", details=None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class BadRequestError(AppError):
    def __init__(self, message="Bad request", details=None):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=400,
            details=details,
        )


class UnauthorizedError(AppError):
    def __init__(self, message="Unauthorized", details=None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details=details,
        )


class ForbiddenError(AppError):
    def __init__(self, message="Forbidden", details=None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=details,
        )


class ConflictError(AppError):
    def __init__(self, message="Conflict", details=None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details,
        )
