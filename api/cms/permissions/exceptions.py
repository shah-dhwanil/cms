from cms.utils.exceptions import CMSException

__all__ = [
    "PermissionNotFoundException",
    "PermissionAlreadyExistsException",
    "PermissionStillReferencedException",
]


class PermissionNotFoundException(CMSException):
    slug = "permission_not_found"
    description = "The requested permission does not exist."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})


class PermissionAlreadyExistsException(CMSException):
    slug = "permission_already_exists"
    description = "A permission with the given parameter already exists."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})


class PermissionStillReferencedException(CMSException):
    slug = "permission_still_referenced"
    description = "The permission is still being referenced by other entities."

    def __init__(self, referenced_by: str, **kwargs):
        super().__init__(context={"referenced_by": referenced_by, **kwargs})
