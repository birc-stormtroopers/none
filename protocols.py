"""Type protocols."""


from __future__ import annotations
from typing import (
    TypeVar,
    Protocol,
    Any,
)


class Ordered(Protocol):
    """Types that support < comparison."""

    def __lt__(self: Ord, other: Ord, /) -> bool:
        """Determine if self is < other."""
        ...


Ord = TypeVar('Ord', bound=Ordered)


class Arithmetic(Protocol):
    """Types that support < comparison."""

    def __add__(self: Arith, other: Any, /) -> Any:
        """Add self and other."""
        ...


Arith = TypeVar('Arith', bound=Arithmetic)
