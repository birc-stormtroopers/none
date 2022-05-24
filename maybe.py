"""Maybe monad."""

from __future__ import annotations

from typing import (
    TypeVar, Generic,
    Callable as Fn,
    Optional as Opt,
)

from dataclasses import dataclass
from functools import wraps
import operator

T = TypeVar('T')
S = TypeVar('S')

Func = Fn[[T], Opt[S]]
OptFunc = Fn[[Opt[T]], Opt[S]]
Op = Fn[[T, T], Opt[T]]
OptOp = Fn[[Opt[T], Opt[T]], Opt[T]]


def bind_func(f: Func[T, S]) -> OptFunc[T, S]:
    """Bind f in the monadic sense."""
    @wraps(f)
    def w(x: Opt[T]) -> Opt[S]:
        return None if x is None else f(x)
    return w


def bind_op(op: Op[T]) -> OptOp[T]:
    """Bind an operator so it returns non-None values if possible."""
    @wraps(op)
    def w(a: Opt[T], b: Opt[T]) -> Opt[T]:
        if a is None:
            return b
        if b is None:
            return a
        return op(a, b)
    return w


def yes(x: T) -> Maybe[T]:
    """Make a maybe that contains a value."""
    return Maybe(x)


def no() -> Maybe[T]:
    """Make a maybe that doesn't contain a value."""
    return Maybe(None)


def val(y: Maybe[T]) -> T:
    """Get a value out of a maybe."""
    if y.val is None:
        raise TypeError("You cannot get the value of a None Maybe")
    return y.val


def bind_cmp(m: Fn[[T, T], bool]) -> Fn[[Maybe[T], Maybe[T] | T], bool]:
    """Return false if either argument is true, otherwise apply op."""
    @wraps(m)
    def w(self: Maybe[T], other: Maybe[T] | T) -> bool:
        if self.val is None:
            return False
        if isinstance(other, Maybe):
            if other.val is None:
                return False
            other = other.val
        return m(self.val, other)
    return w


@dataclass
class Maybe(Generic[T]):
    """Maybe monad."""

    val: Opt[T]

    def __rshift__(self, f: Func[T, S]) -> Maybe[S]:
        """Apply the monadic operator."""
        return Maybe(bind_func(f)(self.val))

    # Do this selectively, somehow...
    __lt__ = bind_cmp(operator.lt)
    __gt__ = bind_cmp(operator.gt)
    ...


def maybe_func(f: Func[T, S]) -> Fn[[Maybe[T]], Maybe[S]]:
    """Bind f in the monadic sense."""
    @ wraps(f)
    def w(x: Maybe[T]) -> Maybe[S]:
        return x >> f
    return w


def maybe_op(op: Op[T]) -> Fn[[Maybe[T], Maybe[T]], Maybe[T]]:
    """Bind an operator so it returns non-None values if possible."""
    @ wraps(op)
    def w(a: Maybe[T], b: Maybe[T]) -> Maybe[T]:
        return Maybe(bind_op(op)(a.val, b.val))
    return w

# Application... binary heap stuff...


def maybe_get(x: list[T], i: int) -> Maybe[tuple[T, int]]:
    """Get value at index i if possible."""
    try:
        return Maybe((x[i], i))
    except IndexError:
        return Maybe(None)


def swap_min_child(x: list[T], p: int) -> None:
    """Swap node p with its smallest child."""
    left = maybe_get(x, 2*p + 1)
    right = maybe_get(x, 2*p + 2)
    f: Op[tuple[T, int]] = min  # type checker is drunk
    smallest = maybe_op(f)(left, right)

    me = maybe_get(x, p)
    if smallest < me:
        _, c = val(smallest)
        print('swapping parent and child...', p, '<->', c)


x = [5.7, 2.1, 3.0, 3.2, 5.9, 6.0]
swap_min_child(x, 0)
swap_min_child(x, 1)
swap_min_child(x, 2)
swap_min_child(x, 3)


# Hack
class M:
    """Class entirely existing for operator overloading."""

    def __matmul__(self, f: Func[T, S]) -> Fn[[Maybe[T]], Maybe[S]]:
        """Bind f in the monadic sense."""
        return maybe_func(f)

    def __add__(self, op: Op[T]) -> Fn[[Maybe[T], Maybe[T]], Maybe[T]]:
        """Bind op in the monadic sense."""
        return maybe_op(op)

    # generic generate these
    def __lt__(self, ab: tuple[Maybe[T], Maybe[S]]) -> bool:
        """Test less than."""
        a, b = ab
        if a.val is None:
            return False
        if b.val is None:
            return False
        return a.val < b.val


m = M()


def f(x): return 2*x


zz = (m @ f)((m @ f)(yes(1)))
yy = (m @ f)(yes(15))
print('zz', zz, 'yy', yy, 'min', (m+min)(zz, yy))
print(m < (zz, yy))
print(m < (zz, no()))
