"""Type protocols."""


from __future__ import annotations
from typing import (
    TypeVar,
    Protocol,
)


class Ordered(Protocol):
    """Types that support < comparison."""

    def __lt__(self: Ord, other: Ord, /) -> bool:
        """Determine if self is < other."""
        ...


Ord = TypeVar('Ord', bound=Ordered)


class Arithmetic(Protocol):
    """Types that support < comparison."""

    def __neg__(self: Arith, /) -> Arith:
        """-self."""
        ...

    def __add__(self: Arith, other: Arith, /) -> Arith:
        """Add self and other."""
        ...

    def __sub__(self: Arith, other: Arith, /) -> Arith:
        """Subtract other from self."""
        ...

    def __mul__(self: Arith, other: Arith, /) -> Arith:
        """Multiply self and other."""
        ...

    def __pow__(self: Arith, other: Arith, /) -> Arith:
        """Raise self to other."""
        ...

    def __truediv__(self: Arith, other: Arith, /) -> Arith:
        """Divide self by other."""
        ...

    def __floordiv__(self: Arith, other: Arith, /) -> Arith:
        """Divide self by other."""
        ...


Arith = TypeVar('Arith', bound=Arithmetic)
