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

T = TypeVar('T')
S = TypeVar('S')
C = TypeVar('C')


# Functions T -> S | Opt[S]
Func = Fn[[T], Opt[S]]
OptFunc = Fn[[Opt[T]], Opt[S]]

# Operators T + T -> S | Opt[S]
Op = Fn[[T, T], Opt[S]]
OptOp = Fn[[Opt[T], Opt[T]], Opt[S]]


def lift_func(f: Func[T, S]) -> OptFunc[T, S]:
    """
    Generalise function to deal with None.

    f'(x) = None if x is None.
    f'(x) = f(x) otherwise.
    """
    @wraps(f)
    def w(x: Opt[T]) -> Opt[S]:
        return None if x is None else f(x)
    return w


def lift_op(op: Op[T, S]) -> OptOp[T, S]:
    """
    Generalise operator to deal with None.

    op'(x,y) = None if either x or y are None.
    op'(x,y) = op(x,y) otherwise.
    """
    @wraps(op)
    def w(a: Opt[T], b: Opt[T]) -> Opt[S]:
        return None if a is None or b is None else op(a, b)
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
    args = tuple(a for a in args if a is not None)
    if not args:
        return None
    assert args[0] is not None  # For the type checker
    res: Opt[T] = args[0]
    for a in args[1:]:
        assert res is not None  # For the type checker
        assert a is not None    # For the type checker
        res = op(res, a)
        if res is None:
            return None
    return res


def unwrap(x: Opt[T]) -> T:
    """Get the value for an optional or throw an exception."""
    if x is None:
        raise ValueError("Must not be None")
    return x

# Hack


class M:
    """Class entirely existing for operator overloading."""

    def __or__(self, f: Func[T, S]) -> OptFunc[T, S]:
        """
        Lift the function f.

        If f: T -> Opt[S] then (m|f): Opt[T] -> Opt[S]
        by propagating None.
        """
        return lift_func(f)

    def __truediv__(self, op: Op[T, S]) -> OptOp[T, S]:
        """
        Lift the operator op.

        If op(T,T) -> Opt[S] then (m/op): (Opt[T],Opt[T]) -> Opt[S]
        by propagating None.
        """
        return lift_op(op)

    def fold(self, f: Op[T, T], *args: Opt[T]) -> Opt[T]:
        """Fold f over args."""
        return fold(f, *args)

    def __matmul__(self, f: Op[T, T]) -> Fn[..., Opt[T]]:
        """Operator for fold."""
        @wraps(f)
        def w(*args: Opt[T]) -> Opt[T]:
            return fold(f, *args)
        return w


m = M()


def f(x: float) -> float:
    """Test."""
    return 2*x


class Ordered(Protocol):
    """Types that support < comparison."""

    def __lt__(self: Ord, other: Any) -> bool:
        """Determine if self is < other."""
        ...


Ord = TypeVar('Ord', bound=Ordered)


def tmin(a: Ord, b: Ord) -> Ord:
    """
    Minimum of a and b.

    Restore some type sanity to Python with this.
    """
    return a if a < b else b


zz: Opt[float] = (m | f)((m | f)(1))
yy: Opt[float] = (m | f)(None)

print('xxx', zz, yy, (m/lt)(zz, yy), (m/lt)(yy, zz))


print('zz', zz, 'yy', yy, 'min', fold(tmin, zz, yy))
print('zz', zz, 'yy', yy, 'min', (m@tmin)(zz, yy))
print((m/lt)(zz, yy))
print((m/lt)(zz, None))


# Application... binary heap stuff...


def maybe_get(x: list[T], i: int) -> Opt[tuple[T, int]]:
    """Get value at index i if possible."""
    try:
        return (x[i], i)
    except IndexError:
        return None


def swap_min_child(x: list[Ord], p: int) -> None:
    """Swap node p with its smallest child."""
    left = maybe_get(x, 2*p + 1)
    right = maybe_get(x, 2*p + 2)
    smallest: Opt[tuple[Ord, int]] = (m@tmin)(left, right)
    print('smallest', smallest)

    me = maybe_get(x, p)
    if (m/lt)(smallest, me):
        _, c = unwrap(smallest)
        print('swapping parent and child...', p, '<->', c)


x = [5.7, 2.1, 3.0, 3.2, 5.9, 6.0]
swap_min_child(x, 0)
swap_min_child(x, 1)
swap_min_child(x, 2)
swap_min_child(x, 3)
