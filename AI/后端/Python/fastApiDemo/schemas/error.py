
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

class SeckillSoldOutError(AppError):
    def __init__(self, message: str = "秒杀已售罄", code: int = 409) -> None:
        super().__init__(message, code)

class SeckillAlreadyBoughtError(AppError):
    def __init__(self, message: str = "您已购买过该商品", code: int = 409) -> None:
        super().__init__(message, code)