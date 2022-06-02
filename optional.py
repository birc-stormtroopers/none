"""Maybe monad."""

from __future__ import annotations
from protocols import (
    Ord
)

from typing import (
    TypeVar,
    Callable as Fn,
    Optional as Opt,
    Any,
    overload
)

from functools import wraps
import operator

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


class IsNone(Exception):
    """Exception when we see an unwanted None."""


def unwrap(x: Opt[_T]) -> _T:
    """
    Get the value for an optional or throw an exception.

    It functions both as the unwrap() method and the ? operator
    in Rust, except that to use it as ? you need to wrap expressions
    in a try...except block at some call level (and the type
    checker cannot check if you really do this).
    """
    if x is None:
        raise IsNone()
    return x


def fold(op: Fn[[_T, _T], Opt[_T]], *args: Opt[_T]) -> Opt[_T]:
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


# Application... binary heap stuff...


# NB. Always False if any arg is None (it will just return None)
lt = lift(operator.lt)


def get(x: list[_T], i: int) -> Opt[_T]:
    """Get value at index i if possible."""
    try:
        return x[i]
    except IndexError:
        return None


def swap_min_child(x: list[Ord], p: int) -> None:
    """Swap node p with its smallest child."""
    me, left, right = get(x, p), get(x, 2*p + 1), get(x, 2*p + 2)
    if lt(left, me) and not lt(right, left):
        x[2*p + 1], x[p] = x[p], x[2*p + 1]
    if lt(right, me) and not lt(left, right):
        x[2*p + 2], x[p] = x[p], x[2*p + 2]

    # child = fold(min, get(x, 2*p + 1), get(x, 2*p + 2))
    # if lift(lt)(child, get(x, p)):
    #     _, c = unwrap(child)  # If child < parent it can't be None
    #     print('swapping parent and child...', p, '<->', c)


# def swap_min_child(x: list[Ord], p: int) -> None:
#     """Swap node p with its smallest child."""
#     child = fold(min, get(x, 2*p + 1), get(x, 2*p + 2))
#     if lift(lt)(child, get(x, p)):
#         _, c = unwrap(child)  # If child < parent it can't be None
#         print('swapping parent and child...', p, '<->', c)


x = [5.7, 2.1, 3.0, 3.2, 5.9, 6.0]
swap_min_child(x, 0)
swap_min_child(x, 1)
swap_min_child(x, 2)
swap_min_child(x, 3)


# def swap_min_child_2(x: list[Ord], p: int) -> None:
#     """Swap node p with its smallest child."""
#     child = fold(min, get(x, 2*p + 1), get(x, 2*p + 2))
#     try:
#         v, c = unwrap(child)
#         if v < x[p]:
#             print('swapping parent and child...', p, '<->', c)

#     except IsNone:
#         pass


# swap_min_child_2(x, 0)
# swap_min_child_2(x, 1)
# swap_min_child_2(x, 2)
# swap_min_child_2(x, 3)
