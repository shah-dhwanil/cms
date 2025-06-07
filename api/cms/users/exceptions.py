from cms.utils.exceptions import BaseException


class UserAlreadyExists(BaseException):
    slug = "user_exists"
    description = "User with given identifier already exists."

    def __init__(self, identifier: str, *args, **kwargs) -> None:
        super().__init__({"identifier": identifier, **kwargs}, *args)


class UserDoesNotExists(BaseException):
    slug = "user_does_not_exists"
    description = "User with given identifier does not exists."

    def __init__(self, identifier: str, *args, **kwargs) -> None:
        super().__init__({"identifier": identifier, **kwargs}, *args)
