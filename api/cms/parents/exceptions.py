from cms.utils.exceptions import CMSException

__all__ = [
    "ParentNotFoundException",
    "ParentAlreadyExistsException",
]


class ParentNotFoundException(CMSException):
    slug = "parent_not_found"
    description = "The requested parent does not exist."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})


class ParentAlreadyExistsException(CMSException):
    slug = "parent_already_exists"
    description = "A parent with the given parameter already exists."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})
