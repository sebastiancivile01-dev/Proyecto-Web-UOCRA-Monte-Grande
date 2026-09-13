"""Router declarativo para conservar el orden actual del menu."""

from collections.abc import Callable


def dispatch(option: str, handlers: dict[str, Callable[[], object]]) -> object:
    handler = handlers.get(option)
    if handler is None:
        raise KeyError(option)
    return handler()
