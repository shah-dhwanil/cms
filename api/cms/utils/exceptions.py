from typing import Any, ClassVar


class BaseException(Exception):
    slug: ClassVar[str]
    description: ClassVar[str]

    def __init__(self, context: dict[str, Any] = dict(), *args) -> None:
        self.context = context
        super().__init__(*args)
