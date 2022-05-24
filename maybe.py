"""Maybe monad."""

from __future__ import annotations

from typing import (
    TypeVar,
    Callable as Fn,
    Optional as Opt,
)

from functools import wraps
import operator

T = TypeVar('T')
S = TypeVar('S')
C = TypeVar('C')

# Functions T -> S | Opt[S]
Func = Fn[[T], Opt[S]]
OptFunc = Fn[[Opt[T]], Opt[S]]

# Operators T + T -> S | Opt[S]
# There are two kinds of these:
# 1) binops like + where any None operand should result in None
# 2) summaries like min(-,-) where if one operand is
#    None we want the other operand (that might be None as well).
Op = Fn[[T, T], Opt[S]]
OptOp = Fn[[Opt[T], Opt[T]], Opt[S]]


def lift_func(f: Func[T, S]) -> OptFunc[T, S]:
    """Generalise function to deal with None."""
    @wraps(f)
    def w(x: Opt[T]) -> Opt[S]:
        return None if x is None else f(x)
    return w


def lift_op(op: Op[T, S]) -> OptOp[T, S]:
    """Generalise operator to deal with None."""
    @wraps(op)
    def w(a: Opt[T], b: Opt[T]) -> Opt[S]:
        return None if a is None or b is None else op(a, b)
    return w


def lift_summary(op: Op[T, T]) -> OptOp[T, T]:
    """Generalise summeration to deal with None."""
    @wraps(op)
    def w(a: Opt[T], b: Opt[T]) -> Opt[T]:
        return b if a is None else a if b is None else op(a, b)
    return w


def unwrap(x: Opt[T]) -> T:
    """Get the value for an optional or throw an exception."""
    if x is None:
        raise ValueError("Must not be None")
    return x

# Hack


def wrap_op(op: Op[T, S]) -> Fn[[C, tuple[Opt[T], Opt[T]]], Opt[S]]:
    """Wrap an operator to something we can use as a method."""
    w = lift_op(op)

    @wraps(op)
    def method(_self: C, ab: tuple[Opt[T], Opt[T]]) -> Opt[S]:
        a, b = ab
        return w(a, b)

    return method


class M:
    """Class entirely existing for operator overloading."""

    def __or__(self, f: Func[T, S]) -> OptFunc[T, S]:
        """Bind f in the monadic sense."""
        return lift_func(f)

    def __matmul__(self, op: Op[T, S]) -> OptOp[T, S]:
        """Bind op in the monadic sense."""
        return lift_op(op)

    def __floordiv__(self, op: Op[T, T]) -> OptOp[T, T]:
        """Bind op in the monadic sense."""
        return lift_summary(op)

    __lt__ = wrap_op(operator.lt)
    __gt__ = wrap_op(operator.gt)
    ...


m = M()


def f(x: float) -> float:
    """Test."""
    return 2*x


zz = (m | f)((m | f)(1))
yy = (m | f)(15)

mymin: Op[float, float] = min
print('zz', zz, 'yy', yy, 'min', (m @ mymin)(zz, yy))
print(m < (zz, yy))
print(m < (zz, None))


# Application... binary heap stuff...


def maybe_get(x: list[T], i: int) -> Opt[tuple[T, int]]:
    """Get value at index i if possible."""
    try:
        return (x[i], i)
    except IndexError:
        return None


def swap_min_child(x: list[T], p: int) -> None:
    """Swap node p with its smallest child."""
    left = maybe_get(x, 2*p + 1)
    right = maybe_get(x, 2*p + 2)
    mi: Op[tuple[T, int], tuple[T, int]] = min
    smallest = (m // mi)(left, right)

    me = maybe_get(x, p)
    if m < (smallest, me):
        _, c = unwrap(smallest)
        print('swapping parent and child...', p, '<->', c)


x = [5.7, 2.1, 3.0, 3.2, 5.9, 6.0]
swap_min_child(x, 0)
swap_min_child(x, 1)
swap_min_child(x, 2)
swap_min_child(x, 3)
