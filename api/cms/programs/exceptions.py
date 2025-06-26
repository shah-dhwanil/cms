from cms.utils.exceptions import CMSException

__all__ = [
    "ProgramNotFoundException",
    "ProgramAlreadyExistsException",
]


class ProgramNotFoundException(CMSException):
    slug = "program_not_found"
    description = "The requested program does not exist."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})


class ProgramAlreadyExistsException(CMSException):
    slug = "program_already_exists"
    description = "A program with the given parameter already exists."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})
