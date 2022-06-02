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

    def __add__(self: Arith, other: Arith, /) -> Any:
        """Add self and other."""
        ...

    def __sub__(self: Arith, other: Arith, /) -> Any:
        """Subtract other from self."""
        ...

    def __mul__(self: Arith, other: Arith, /) -> Any:
        """Multiply self and other."""
        ...

    def __truediv__(self: Arith, other: Arith, /) -> Any:
        """Divide self by other."""
        ...


Arith = TypeVar('Arith', bound=Arithmetic)
