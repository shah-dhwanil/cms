from cms.utils.exceptions import BaseException


class ParentDoesNotExists(BaseException):
    slug = "parent_does_not_exists"
    description = "Parent does not exists"

    def __init__(self, identifier: str, *args, **kwargs) -> None:
        super().__init__({"identifier": identifier, **kwargs}, *args)


class ParentAlreadyExists(BaseException):
    slug = "parent_already_exists"
    description = "Parent already exists"

    def __init__(self, identifier: str, *args, **kwargs) -> None:
        super().__init__({"identifier": identifier, **kwargs}, *args)
