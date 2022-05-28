"""
A Maybe monad.

A monad is an idea from category theory that is used extensively
in pure functional languages like Haskell. It is an abstract
concept with many uses, from I/O to handling optinal values
like we do here.

A monad consists of an extended type `M[T]` (The monad `M` over type `T`)
and two functions:

The function `unit` or `return`

    unit: T -> M[T]

that sends a T value into the monad, and the function `bind`
(I don't know why it has this name, it applies) that applies
a function on a monad value

    bind: M[T] -> (T -> M[S]) -> M[S]

it takes a `M[T]` value, `a` and a function that sends a `T` value
to `M[S]`, `f`, and then it gives us `f(a')` if `a'` is a `T` value
underlying the `a` value in `M[T]` and something else in `M[S]`
otherwise.

To make it more concrete, let's say we have a type `T` and we want
to handle something like `T` + `None`. (Python already allows this
for all `T` types, but we will fix an issue with that). We call the
monad `Maybe` and it can have two types of values, `Some(a)` for
values `a` from `T` or `Nothing`.

We can send `T` values into `Maybe[T]` with

def unit(a: T) -> Maybe[T]:
    return Some(a)

and if we want to apply (or bind) a function we have

def bind(a: Maybe[T], f: Fn[[T], Maybe[S]]) -> Maybe[S]:
    match a:
        case Nothing:
            return Nothing
        case Some(a_):
            return f(a_)

The `bind()` function is usually implemented as an infix
operator, `>>=`, so we would apply it as

    a >>= lambda a_: Some(...)

or something to that effect. We can't use >>= in Python
because that is only allowed as a statement, but we could
use >>.

"""

from __future__ import annotations
from inspect import (
    signature
)
import operator
from typing import (
    TypeVar,
    Generic, Protocol,
    Callable as Fn,
    Any,
    runtime_checkable
)
from functools import wraps


T = TypeVar('T')
S = TypeVar('S')
R = TypeVar('R')

# Handling operator protocols


@runtime_checkable
class Ordered(Protocol):
    """Types that support < comparison."""

    def __lt__(self: Ord, other: Any) -> bool:
        """Determine if self is < other."""
        ...


@runtime_checkable
class Arithmetic(Protocol):
    """Types that support < comparison."""

    def __add__(self: Arith, other: Any) -> Arith:
        """Add self and other."""
        ...


Ord = TypeVar('Ord', bound=Ordered)
Arith = TypeVar('Arith', bound=Arithmetic)


class IsNothing(Exception):
    """Exception raised if we try to get the value of Nothing."""


def _lift(f: Fn[..., R]) -> Fn[..., Maybe[R]]:
    """Lift f to work on Maybe."""
    @wraps(f)
    def w(*args: Maybe[Any]) -> Maybe[R]:
        try:
            return Some(f(*(a.unwrap() for a in args)))
        except IsNothing:
            return Nothing
    return w


class Maybe(Generic[T]):
    """Maybe monad over T."""

    def __rshift__(self, _f: Fn[[T], Maybe[R]]) -> Maybe[R]:
        """Bind and apply f."""
        ...

    def unwrap(self) -> T:
        """Return the wrapped value or raise an exception."""
        ...

    # FIXME: The type checking isn't working properly here...
    # The type of the operators isn't right, and the lifted op
    # isn't checked against what ops T has. The latter is
    # hard to do when Maybe is dynamic and the type checking
    # is static...
    __lt__ = _lift(operator.lt)
    __add__ = _lift(operator.lt)


class Some(Maybe[T]):
    """Objects containing values."""

    _val: T

    def __init__(self, val: T) -> None:
        """Create a new monadic value."""
        self._val = val

    def __repr__(self) -> str:
        """Get repr for Maybe[T]."""
        return f"Some({self._val})"

    def __bool__(self) -> bool:
        """Return true if val is true."""
        return bool(self._val)

    def __rshift__(self, f: Fn[[T], Maybe[R]]) -> Maybe[R]:
        """Bind and apply f."""
        return f(self._val)

    def unwrap(self) -> T:
        """Return the wrapped value or raise an exception."""
        return self._val


class Nothing_(Maybe[Any]):
    """Nothing to see here."""

    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any) -> Nothing_:
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def __repr__(self) -> str:
        """Nothing is nothing."""
        return "Nothing"

    def __bool__(self) -> bool:
        """Nothing is always false."""
        return False

    def __rshift__(self, _f: Fn[[T], Maybe[R]]) -> Maybe[R]:
        """Bind and apply f."""
        return Nothing

    def unwrap(self) -> T:
        """Return the wrapped value or raise an exception."""
        raise IsNothing("tried to unwrap a Nothing value")


Nothing = Nothing_()


x: Maybe[int] = Some(1)
y: Maybe[int] = Nothing
print(x, y)

z = x >> (lambda a: Some(2*a)) >> (lambda a: Some(-a))
print(z)

z = y >> (lambda a: Some(2*a)) >> (lambda a: Some(-a))
print(z)

# Operators require currying
z = x >> (lambda a: y >> (lambda b: Some(a+b)))
print(z)

z = x >> (lambda a: x >> (lambda b: Some(a+b)))
print(z)


# Operator overloading
print('sig lt', signature(Maybe.__lt__))
print('sig add', signature(Maybe.__add__))


print('add', x + x)
print('add', x + y)
print('lt', x < y)
print('lt', z < x)
print('lt', x < Some(12))
