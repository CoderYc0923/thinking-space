
class AppError(Exception):
    def __init__(self, message: str, code: int = 400) -> None:
        self.message = message
        self.code = code
        super().__init__(message)

class NotFoundError(AppError):
    def __init__(self, message: str = "资源未找到", code: int = 404) -> None:
        super().__init__(message, code)

class ConflictError(AppError):
    def __init__(self, message: str = "资源冲突", code: int = 409) -> None:
        super().__init__(message, code)