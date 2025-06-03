from cms.utils.exceptions import BaseException


class PermissionAlreadyExists(BaseException):
    slug = "permission_already_exists"
    description = "The permission already exists"


class PermissionDoesNotExist(BaseException):
    slug = "permission_does_not_exist"
    description = "The permission does not exist"


class PermissionReferenced(BaseException):
    slug = "permission_referenced"
    description = "The permission is still being referenced by a entity, thus can't perform the action"

    def __init__(self, action: str, *args, **kwargs) -> None:
        super().__init__({"action": action, **kwargs}, *args)
