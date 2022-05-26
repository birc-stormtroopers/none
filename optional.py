"""Maybe monad."""

from __future__ import annotations

from typing import (
    TypeVar,
    Protocol,
    Callable as Fn,
    Optional as Opt,
    Any
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

Fun = Fn[[T], Opt[R]]
Fun2 = Fn[[T, S], Opt[R]]
LiftFun = Fn[[Opt[T]], Opt[R]]
LiftFun2 = Fn[[Opt[T], Opt[S]], Opt[R]]


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


def lift_func(f: Fun[T, R]) -> LiftFun[T, R]:
    """
    Generalise function to deal with None.

    f'(x) = None if x is None.
    f'(x) = f(x) otherwise.
    """
    @wraps(f)
    def w(x: Opt[T]) -> Opt[R]:
        return None if x is None else f(x)
    return w


def lift_op(op: Fun2[T, S, R]) -> LiftFun2[T, S, R]:
    """
    Generalise operator to deal with None.

    op'(x,y) = None if either x or y are None.
    op'(x,y) = op(x,y) otherwise.
    """
    @wraps(op)
    def w(a: Opt[T], b: Opt[S]) -> Opt[R]:
        return None if a is None or b is None else op(a, b)
    return w


def fold(op: Fun2[T, T, T], *args: Opt[T]) -> Opt[T]:
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


# Hack


class LiftOpt:
    """Class entirely existing for operator overloading."""

    def __truediv__(self, f: Fun[T, S]) -> LiftFun[T, S]:
        """
        Lift the function f.

        If f: T -> Opt[S] then (lift/f): Opt[T] -> Opt[S]
        by propagating None.
        """
        return lift_func(f)

    def __floordiv__(self, op: Fun2[T, S, R]) -> LiftFun2[T, S, R]:
        """
        Lift the operator op.

        If op(T,S) -> Opt[R] then (lift//op): (Opt[T],Opt[S]) -> Opt[R]
        by propagating None.
        """
        return lift_op(op)

    def fold(self, f: Fun2[T, T, T], *args: Opt[T]) -> Opt[T]:
        """Fold f over args."""
        return fold(f, *args)


lift = LiftOpt()


def f(x: float) -> float:
    """Test."""
    return 2*x


zz: Opt[float] = (lift/f)((lift/f)(1.2))
yy: Opt[float] = (lift/f)(42)
ww: Opt[float] = (lift/f)(None)

print('xxx', zz, yy,
      (lift//lt)(zz, yy), (lift//lt)(yy, zz),
      (lift//lt)(yy, ww))

foo = fold(min, zz, yy)
bar = lift.fold(min, zz, ww)
print('zz', zz, 'yy', yy, 'min', foo, bar)
print((lift//lt)(zz, yy))
print((lift//lt)(zz, None))


# Application... binary heap stuff...


def get(x: list[T], i: int) -> Opt[tuple[T, int]]:
    """Get value at index i if possible."""
    try:
        return (x[i], i)
    except IndexError:
        return None


def swap_min_child(x: list[Ord], p: int) -> None:
    """Swap node p with its smallest child."""
    child = lift.fold(min, get(x, 2*p + 1), get(x, 2*p + 2))
    if (lift//lt)(child, get(x, p)):
        _, c = unwrap(child)  # If child < parent it can't be None
        print('swapping parent and child...', p, '<->', c)


x = [5.7, 2.1, 3.0, 3.2, 5.9, 6.0]
swap_min_child(x, 0)
swap_min_child(x, 1)
swap_min_child(x, 2)
swap_min_child(x, 3)


def swap_min_child_2(x: list[Ord], p: int) -> None:
    """Swap node p with its smallest child."""
    child = lift.fold(min, get(x, 2*p + 1), get(x, 2*p + 2))
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
