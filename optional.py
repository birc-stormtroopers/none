"""Maybe monad."""

from __future__ import annotations

from typing import (
    TypeVar,
    Protocol,
    Callable as Fn,
    Optional as Opt,
    Any,
    overload
)

from functools import wraps
from operator import lt


class Ordered(Protocol):
    """Types that support < comparison."""

    def __lt__(self: Ord, other: Any) -> bool:
        """Determine if self is < other."""
        ...


Ord = TypeVar('Ord', bound=Ordered)

T = TypeVar('T')
S = TypeVar('S')
R = TypeVar('R')


class IsNone(Exception):
    """Exception when we see an unwanted None."""


def unwrap(x: Opt[T]) -> T:
    """
    Get the value for an optional or throw an exception.

    It functions both as the unwrap() method and the ? operator
    in Rust, except that to use it as ? you need to wrap expressions
    in a try...except block.
    """
    if x is None:
        raise IsNone()
    return x


@overload
def lift(f: Fn[[T], Opt[R]]) -> Fn[[Opt[T]], Opt[R]]:
    """Lift function f."""
    ...


@overload
def lift(f: Fn[[T, S], Opt[R]]) -> Fn[[Opt[T], Opt[S]], Opt[R]]:
    """Lift function f."""
    ...


def lift(f: Fn[..., Opt[R]]) -> Fn[..., Opt[R]]:
    """Lift a generic function."""
    @wraps(f)
    def w(*args: Any, **kwargs: Any) -> Opt[R]:
        if None in args or None in kwargs.values():
            return None
        return f(*args, **kwargs)
    return w


def fold(op: Fn[[T, T], Opt[T]], *args: Opt[T]) -> Opt[T]:
    """
    Generalise a fold over the operator by tossing away None.

    After we have removed all None we will return None if the
    resulting list is empty, the singleton element if there is one,
    and otherwise apply op to all the elements left to right.
    If the op returns None at any point that is also the final
    result.
    """
    try:  # try-block because of unwrap()

        non_none = tuple(a for a in args if a is not None)
        if not non_none:
            return None

        res = non_none[0]
        for a in non_none[1:]:
            res = unwrap(op(res, a))
        return res

    except IsNone:
        return None


# notation hack
ƛ = lift


def f(x: float) -> float:
    """Test."""
    return 2*x


zz: Opt[float] = ƛ(f)(ƛ(f)(1.2))
yy: Opt[float] = ƛ(f)(42)
ww: Opt[float] = ƛ(f)(None)

print('xxx', zz, yy,
      ƛ(lt)(zz, yy), ƛ(lt)(yy, zz),
      ƛ(lt)(yy, ww))

foo = fold(min, zz, yy)
print('zz', zz, 'yy', yy, 'min', foo)
print(ƛ(lt)(zz, yy))
print(ƛ(lt)(zz, None))


# Application... binary heap stuff...


def get(x: list[T], i: int) -> Opt[tuple[T, int]]:
    """Get value at index i if possible."""
    try:
        return (x[i], i)
    except IndexError:
        return None


def swap_min_child(x: list[Ord], p: int) -> None:
    """Swap node p with its smallest child."""
    child = fold(min, get(x, 2*p + 1), get(x, 2*p + 2))
    if ƛ(lt)(child, get(x, p)):
        _, c = unwrap(child)  # If child < parent it can't be None
        print('swapping parent and child...', p, '<->', c)


x = [5.7, 2.1, 3.0, 3.2, 5.9, 6.0]
swap_min_child(x, 0)
swap_min_child(x, 1)
swap_min_child(x, 2)
swap_min_child(x, 3)


def swap_min_child_2(x: list[Ord], p: int) -> None:
    """Swap node p with its smallest child."""
    child = fold(min, get(x, 2*p + 1), get(x, 2*p + 2))
    try:
        v, c = unwrap(child)
        if v < x[p]:
            print('swapping parent and child...', p, '<->', c)

    except IsNone:
        pass


swap_min_child_2(x, 0)
swap_min_child_2(x, 1)
swap_min_child_2(x, 2)
swap_min_child_2(x, 3)
