from cms.utils.exceptions import BaseException


class StudentDoesNotExists(BaseException):
    slug = "student_does_not_exists"
    description = "Student with given identifier does not exists."

    def __init__(self, identifier: str, *args, **kwargs) -> None:
        super().__init__({"identifier": identifier, **kwargs}, *args)


class StudentAlreadyExists(BaseException):
    slug = "student_already_exists"
    description = "Student with given identifier already exists."

    def __init__(self, identifier: str, *args, **kwargs) -> None:
        super().__init__({"identifier": identifier, **kwargs}, *args)
