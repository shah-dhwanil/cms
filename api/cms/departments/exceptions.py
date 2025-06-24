from cms.utils.exceptions import CMSException

__all__ = [
    "DepartmentNotFoundException",
    "DepartmentAlreadyExistsException",
]


class DepartmentNotFoundException(CMSException):
    slug = "department_not_found"
    description = "The requested department does not exist."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})


class DepartmentAlreadyExistsException(CMSException):
    slug = "department_already_exists"
    description = "A department with the given parameter already exists."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})
