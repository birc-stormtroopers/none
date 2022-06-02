"""Testing type constructions."""

from typing import (
    TypeVar, ParamSpec,
    Callable as Fn,
    Optional as Opt,
    Any,
    overload
)
from functools import wraps
import math

_T = TypeVar('_T')
_R = TypeVar('_R')

_1 = TypeVar('_1')
_2 = TypeVar('_2')
_3 = TypeVar('_3')
_4 = TypeVar('_4')

_P = ParamSpec('_P')


@overload
def lift(f: Fn[[_1], Opt[_R]]) -> Fn[[Opt[_1]], Opt[_R]]:
    """Lift function f."""
    ...


@overload
def lift(f: Fn[[_1, _2], Opt[_R]]) -> Fn[[Opt[_1], Opt[_2]], Opt[_R]]:
    """Lift function f."""
    ...


@overload
def lift(f: Fn[[_1, _2, _3], Opt[_R]]) \
        -> Fn[[Opt[_1], Opt[_2], Opt[_3]], Opt[_R]]:
    """Lift function f."""
    ...


@overload
def lift(f: Fn[[_1, _2, _3, _4], Opt[_R]]) \
        -> Fn[[Opt[_1], Opt[_2], Opt[_3], Opt[_4]], Opt[_R]]:
    """Lift function f."""
    ...


def lift(f: Fn[..., Opt[_R]]) -> Fn[..., Opt[_R]]:
    """Lift a generic function."""
    @wraps(f)
    def w(*args: Any, **kwargs: Any) -> Opt[_R]:
        if None in args or None in kwargs.values():
            return None
        return f(*args, **kwargs)
    return w


def catch_to_none(f: Fn[_P, _R]) -> Fn[_P, Opt[_R]]:
    """Wrap a function so it returns None instead of an exception."""
    @wraps(f)
    def w(*args: _P.args, **kwargs: _P.kwargs) -> Opt[_R]:
        try:
            return f(*args, **kwargs)
        except Exception:
            return None
    return w


def roots(a: float, b: float, c: float) -> Opt[tuple[float, float]]:
    """Get the roots of the quadratic equation ax**2 + bx + c."""

    @catch_to_none
    def sqrt(x: float) -> float:
        return math.sqrt(x)

    @catch_to_none  # We could divide by zero
    @lift           # sq could be None
    def _roots(sq: float) -> tuple[float, float]:
        return (-b - sq) / (2*a), (-b + sq) / (2*a)

    return _roots(sqrt(b**2 - 4*a*c))


x = roots(0, 0, 0)
print(x)
