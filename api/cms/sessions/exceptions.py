from cms.utils.exceptions import CMSException

__all__ = [
    "SessionNotFoundException",
]


class SessionNotFoundException(CMSException):
    slug = "session_not_found"
    description = "The requested session does not exist."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})
