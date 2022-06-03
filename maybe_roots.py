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


def sqrt(x: Maybe[float]) -> Maybe[float]:
    """Compute the square root if x >= 0."""
    return Maybe.do(
        Some(math.sqrt(a)) if a >= 0 else Nothing
        for a in x
    )


def roots(a_: float, b_: float, c_: float
          ) -> tuple[Maybe[float], Maybe[float]]:
    """Get the roots of the quadratic equation ax**2 + bx + c."""
    a, b, c = Some(a_), Some(b_), Some(c_)
    sq = sqrt(b**Some(2.0) - Some(4.0)*a*c)
    return ((-b - sq) / (Some(2.0)*a), (-b + sq) / (Some(2.0)*a))
