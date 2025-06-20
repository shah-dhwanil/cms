from cms.utils.exceptions import CMSException

__all__ = [
    "StaffNotFoundException",
    "StaffAlreadyExistsException",
]


class StaffNotFoundException(CMSException):
    slug = "staff_not_found"
    description = "The requested staff member does not exist."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})


class StaffAlreadyExistsException(CMSException):
    slug = "staff_already_exists"
    description = "A staff member with the given parameter already exists."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})
