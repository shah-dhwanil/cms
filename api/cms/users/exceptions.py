from cms.utils.exceptions import CMSException


__all__ = [
    "UserNotFoundException",
    "UserAlreadyExistsException",
    "PasswordIncorrectException",
]


class UserNotFoundException(CMSException):
    slug = "user_not_found"
    description = "The requested user does not exist."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})


class UserAlreadyExistsException(CMSException):
    slug = "user_already_exists"
    description = "A user with the given parameter already exists."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})


class PasswordIncorrectException(CMSException):
    slug = "password_incorrect"
    description = "The password entered is incorrect"
