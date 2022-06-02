"""Computing the roots of a quadratic equation."""

from typing import (
    TypeVar, ParamSpec,
    Callable as Fn,
    Optional as Opt,
)
from optional import lift
from functools import wraps
import math
import operator

_P = ParamSpec('_P')
_R = TypeVar('_R')


def catch_to_none(f: Fn[_P, _R]) -> Fn[_P, Opt[_R]]:
    """Wrap a function so it returns None instead of an exception."""
    @wraps(f)
    def w(*args: _P.args, **kwargs: _P.kwargs) -> Opt[_R]:
        try:
            return f(*args, **kwargs)
        except Exception:
            return None
    return w


@lift
def neg(x: float) -> float:
    """Return -x."""
    # can't use operator.neg bcs type binding
    return x


sub = lift(operator.sub)
add = lift(operator.add)
mul = lift(operator.mul)


@lift
def div(a: float, b: float) -> Opt[float]:
    """Return a/b or None if b is zero."""
    return None if b == 0 else a / b


@catch_to_none  # math.sqrt() might throw ValueError
def sqrt(x: float) -> float:
    """Return sqrt of x or None if not defined."""
    return math.sqrt(x)


def roots(a: float, b: float, c: float) -> tuple[Opt[float], Opt[float]]:
    """Get the roots of the quadratic equation ax**2 + bx + c."""
    sq = sqrt(b**2 - 4*a*c)
    return div(sub(neg(b), sq), mul(2, a)), div(add(neg(b), sq), mul(2, a))


def roots2(a: float, b: float, c: float) -> Opt[tuple[float, float]]:
    """Get the roots of the quadratic equation ax**2 + bx + c."""
    @catch_to_none  # We could divide by zero
    @lift           # sq could be None
    def _roots(sq: float) -> tuple[float, float]:
        return (-b - sq) / (2*a), (-b + sq) / (2*a)

    return _roots(sqrt(b**2 - 4*a*c))


@catch_to_none
def roots3(a: float, b: float, c: float) -> tuple[float, float]:
    """Get the roots of the quadratic equation ax**2 + bx + c."""
    sq = math.sqrt(b**2 - 4*a*c)
    return (-b - sq) / (2*a), (-b + sq) / (2*a)
