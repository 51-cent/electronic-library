class ApplicationError(Exception):
    status_code = 500

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class NotFoundError(ApplicationError):
    status_code = 404


class ConflictError(ApplicationError):
    status_code = 409


class AuthenticationError(ApplicationError):
    status_code = 401
    headers = {'WWW-Authenticate': 'Bearer'}


class ForbiddenError(ApplicationError):
    status_code = 403
