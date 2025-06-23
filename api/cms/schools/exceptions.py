from cms.utils.exceptions import CMSException

# filepath: /workspaces/cms/api/cms/schools/exceptions.py


__all__ = [
    "SchoolNotFoundException",
    "SchoolAlreadyExistsException",
]


class SchoolNotFoundException(CMSException):
    slug = "school_not_found"
    description = "The requested school does not exist."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})


class SchoolAlreadyExistsException(CMSException):
    slug = "school_already_exists"
    description = "A school with the given parameter already exists."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})
