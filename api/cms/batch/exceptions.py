from cms.utils.exceptions import CMSException

# filepath: /workspaces/cms/api/cms/batch/exceptions.py


__all__ = [
    "BatchNotFoundException",
    "BatchAlreadyExistsException",
]


class BatchNotFoundException(CMSException):
    slug = "batch_not_found"
    description = "The requested batch does not exist."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})


class BatchAlreadyExistsException(CMSException):
    slug = "batch_already_exists"
    description = "A batch with the given parameter already exists."

    def __init__(self, parameter: str, **kwargs):
        super().__init__(context={"parameter": parameter, **kwargs})
