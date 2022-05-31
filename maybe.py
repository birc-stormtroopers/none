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
    TypeVar, ParamSpec,
    Generic, Protocol,
    Callable as Fn,
    Any,
)
from functools import wraps


T = TypeVar('T')
S = TypeVar('S')
R = TypeVar('R')

P = ParamSpec('P')

# Handling operator protocols


class Ordered(Protocol):
    """Types that support < comparison."""

    def __lt__(self: Ord, other: Ord) -> bool:
        """Determine if self is < other."""
        ...


class Arithmetic(Protocol):
    """Types that support < comparison."""

    def __add__(self: Arith, other: Any) -> Any:
        """Add self and other."""
        ...


Ord = TypeVar('Ord', bound=Ordered)
Arith = TypeVar('Arith', bound=Arithmetic)


def f(x: Ord) -> None:
    """Do nothing."""
    print('nothing done,', x)


class Bar:
    """Nothing to see here."""


f(1)
f("foo")
# f(lambda x: x) # type error, ok
# f(Bar)         # type error, ok
# f(Bar())       # type error, ok

X = TypeVar('X', int, float, str)


class Wrap(Generic[T]):
    """Wrap a value of type T."""

    val: T

    def __init__(self, val: T) -> None:
        """Wrap a value."""
        self.val = val

    def __lt__(self: Wrap[X], other: Wrap[X]) -> bool:
        """Compare wrapped."""
        return self.val < other.val

    def f(self: Wrap[T], _x: Wrap[Ord]) -> None:
        """Test."""
        return

    def g(self: Wrap[Ord], _x: Wrap[S]) -> None:
        """Test."""
        return


# these should be okay since _x is Wrap[int] so Wrap[Ord]
Wrap(1).f(Wrap(1))    # Ok
Wrap(Bar).f(Wrap(1))  # Ok

# these should not be okay since _x is Wrap[Bar]
Wrap(1).f(Wrap(Bar))      # Error -- which we want
Wrap("foo").f(Wrap(Bar))  # Error -- which we want

# These should be okay since self is Wrap[int]
Wrap(1).g(Wrap(1))    # Ok
Wrap(1).g(Wrap(Bar))  # Ok, _x is Wrap[S] but that's fine

# These should not okay since self is Wrap[Bar] which isn't Wrap[Ord]
Wrap(Bar).g(Wrap(1))    # Ok, but *shouldn't be*
Wrap(Bar).g(Wrap(Bar))  # Ok, but *shouldn't be*


print(Wrap(1) < Wrap(2))                      # type error
print(Wrap("foo") < Wrap("bar"))              # type error
print(Wrap(lambda x: x) < Wrap(lambda x: x))  # type error
print(Wrap(Bar) < Wrap(Bar))                  # type error
print(Wrap(Bar()) < Wrap(Bar()))              # type error


class IsNothing(Exception):
    """Exception raised if we try to get the value of Nothing."""


def _lift_ret(f: Fn[P, R]) -> Fn[P, Maybe[R]]:
    """Lift f to return a Maybe."""
    @ wraps(f)
    def w(*args: P.args, **kwargs: P.kwargs) -> Maybe[R]:
        return Some(f(*args, **kwargs))
    return w


def _lift(f: Fn[..., R]) -> Fn[..., Maybe[R]]:
    """Lift f to work on Maybe."""
    @ wraps(f)
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

    # FIXME: There is a bug in mypy https://github.com/python/mypy/issues/11167
    # that prevents the propert type checking of wrapped types, so I cannot
    # ensure that an operator is only valid if the underlying type supports it.
    # The second I add an operator to this class, mypy thinks that all wrapped
    # types support it. Stupid mypy!
    _lt = _lift(operator.lt)

    def __lt__(self: Maybe[Ord], other: Maybe[Ord]) -> Maybe[bool]:
        """Compare with other."""
        return self._lt(other)

    _add = _lift(operator.add)

    def __add__(self: Maybe[Arith], other: Maybe[T]) -> Maybe[R]:
        """Add self with other."""
        return self._add(other)


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


# Try with lifting a function
def mult13(x: int) -> int:
    """Test function for lifting."""
    return 13 * x


ƛ = _lift_ret
z = x >> ƛ(mult13)
print(z)
z = y >> ƛ(mult13)
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
