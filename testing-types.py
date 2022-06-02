from typing import (
    TypeVar,
    Callable as Fn,
    Optional as Opt,
    Any,
    overload
)
from functools import wraps

_T = TypeVar('_T')
_R = TypeVar('_R')

_1 = TypeVar('_1')
_2 = TypeVar('_2')
_3 = TypeVar('_3')
_4 = TypeVar('_4')


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


def f(x: _T) -> _T:
    return x


def apply(x: _T, f: Fn[[_T], _T]) -> Opt[_T]:
    ff = lift(f)  # Lift's ff, but here _T will be bound to apply's _T
    return ff(x)  # This will be Opt[_T] for the bound _T


reveal_type(apply(12, f))      # An Opt[int] because x is int
reveal_type(apply("foo", f))   # An Opt[str] because x is str
