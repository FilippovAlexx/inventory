class BaseError(Exception):
    def __init__(self, *, message: str):
        super().__init__()
        self.message = message


class HTTPError(BaseError):
    def __init__(self, *, status_code: int, message: str):
        super().__init__(message=message)
        self.status_code = status_code


class InvalidSecretError(BaseError):
    ...


class UserExistsError(BaseError):
    ...
