from cms.utils.exceptions import CMSException

__all__ = [
    "StudentNotFoundException",
    "StudentAlreadyExistsException",
]


class StudentNotFoundException(CMSException):
    slug = "student_not_found"
    description = "The requested student does not exist."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})


class StudentAlreadyExistsException(CMSException):
    slug = "student_already_exists"
    description = "A student with the given parameter already exists."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})
