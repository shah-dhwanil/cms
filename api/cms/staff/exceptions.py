from cms.utils.exceptions import BaseException


class StaffDoesNotExists(BaseException):
    slug = "staff_does_not_exists"
    description = "Staff does not exists"

    def __init__(self, identifier: str, *args, **kwargs) -> None:
        super().__init__({"identifier": identifier, **kwargs}, *args)


class StaffAlreadyExists(BaseException):
    slug = "staff_already_exists"
    description = "Staff Already Exists"

    def __init__(self, identifier: str, *args, **kwargs) -> None:
        super().__init__({"identifier": identifier, **kwargs}, *args)
