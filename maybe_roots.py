"""Computing the roots of a quadratic equation."""

from typing import (
    TypeVar
)
from maybe import (
    Maybe, Some, Nothing
)
import math

_T = TypeVar('_T')
_R = TypeVar('_R')


def inv(x: float) -> Maybe[float]:
    """Return 1/x if x != 0."""
    return Nothing if x == 0 else Some(1/x)


def sqrt(x: float) -> Maybe[float]:
    """Compute the square root if x >= 0."""
    return Some(math.sqrt(x)) if x >= 0 else Nothing


def roots(a: float, b: float, c: float) -> Maybe[tuple[float, float]]:
    """Get the roots of the quadratic equation ax**2 + bx + c."""
    return Maybe.do(
        ((-b - sq) / i, (-b + sq) / i)
        for i in inv(2 * a)
        for sq in sqrt(b**2 - 4*a*c)
    )
