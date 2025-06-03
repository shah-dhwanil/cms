from cms.utils.exceptions import BaseException


class SessionDoesNotExists(BaseException):
    slug = "session_does_not_exists"
    message = "Session does not exists"
