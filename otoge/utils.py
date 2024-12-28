from inspect import signature as _signature
from typing import Callable, Any, TypeVar

__all__ = ("copydoc",)

T = TypeVar("T")


def copydoc(original: Callable[..., Any]) -> Callable[[T], T]:
    def decorator(overridden: T) -> T:
        overridden.__doc__ = original.__doc__
        overridden.__signature__ = _signature(original)  # type: ignore
        return overridden

    return decorator
