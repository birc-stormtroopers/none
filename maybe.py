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

from abc import (
    ABC,
    abstractmethod
)
from typing import (
    Iterator, Generator,
    TypeVar,
    Generic,
    Callable as Fn,
    Final,
    Any,
)
from protocols import (
    Ord, Arith,
)

_T = TypeVar('_T')
_R = TypeVar('_R')

_K = TypeVar('_K')
_V = TypeVar('_V')


class IsNothing(Exception):
    """Exception raised if we try to get the value of Nothing."""


class Maybe(Generic[_T], ABC):
    """Maybe monad over T."""

    @abstractmethod
    def __rshift__(self, _f: Fn[[_T], Maybe[_R]]) -> Maybe[_R]:
        """Bind and apply f."""
        ...

    @abstractmethod
    def unwrap(self) -> _T:
        """Return the wrapped value or raise an exception."""
        ...

    def unwrap_or(self, _x: _T) -> _T:
        """Return the wrapped value or give us x if it is Nothing."""
        ...

    def __bool__(self) -> bool:
        """Make sure we don't use a Maybe as a bool."""
        assert False, "A Maybe is not a truth-value."
        return False

    # do syntactic sugar
    def __iter__(self) -> Iterator[_T]:
        """Let's us unwrap in a for-loop."""
        yield self.unwrap()

    @classmethod
    def do(cls, expr: Generator[_R | Maybe[_R], None, None]) -> Maybe[_R]:
        """Evaluate do-expression.

        Add two numbers with

        >>> Maybe.do(a - b for a in Some(44) for b in Some(2))
        Some(42)

        If the expression evaluates to a Maybe, we don't lift it but
        propagate it as it is:

        >>> Maybe.do(Nothing if b == 0 else Some(a/b)
        ...          for a in Some(44) for b in Some(0))
        Nothing
        >>> Maybe.do(Nothing if b == 0 else Some(a/b)
        ...          for a in Some(44) for b in Some(2))
        Some(22.0)

        """
        try:
            res = next(expr)
            return res if isinstance(res, Maybe) else Some(res)
        except IsNothing:
            return Nothing

    # Operator overloading. Type checking doesn't work with mypy, who thinks
    # that any type is just fine even when self is constraint, but it does
    # work with pyright/pylance.

    # Some comparison operators...
    def __lt__(self: Maybe[Ord], other: Maybe[Ord]) -> Maybe[bool]:
        """Test less than, if _T is Ord."""
        return Maybe.do(a < b for a in self for b in other)

    # Some arithmetic operators...
    def __neg__(self: Maybe[Arith]) -> Maybe[Arith]:
        """-self."""
        return Maybe.do(-a for a in self)

    def __add__(self: Maybe[Arith], other: Maybe[Arith]) -> Maybe[Arith]:
        """Add, if _T is Arith."""
        return Maybe.do(a + b for a in self for b in other)

    def __sub__(self: Maybe[Arith], other: Maybe[Arith]) -> Maybe[Arith]:
        """Add, if _T is Arith."""
        return Maybe.do(a - b for a in self for b in other)

    def __mul__(self: Maybe[Arith], other: Maybe[Arith]) -> Maybe[Arith]:
        """Multiply, if _T is Arith."""
        return Maybe.do(a * b for a in self for b in other)

    def __pow__(self: Maybe[Arith], other: Maybe[Arith]) -> Maybe[Arith]:
        """Raise self to other."""
        return Maybe.do(a**b for a in self for b in other)

    def __truediv__(self: Maybe[Arith], other: Maybe[Arith]) -> Maybe[Arith]:
        """Divide, if _T is Arith."""
        return Maybe.do(Nothing if b == 0 else Some(a/b)
                        for a in self for b in other)

    def __floordiv__(self: Maybe[Arith], other: Maybe[Arith]) -> Maybe[Arith]:
        """Divide, if _T is Arith."""
        return Maybe.do(Nothing if b == 0 else Some(a//b)
                        for a in self for b in other)


class Some(Maybe[_T]):
    """Objects containing values."""

    _val: _T
    __match_args__ = ('_val')

    def __init__(self, val: _T) -> None:
        """Create a new monadic value."""
        self._val = val

    def __repr__(self) -> str:
        """Get repr for Maybe[_T]."""
        return f"Some({self._val})"

    def __rshift__(self, f: Fn[[_T], Maybe[_R]]) -> Maybe[_R]:
        """Bind and apply f."""
        return f(self._val)

    def unwrap(self) -> _T:
        """Return the wrapped value or raise an exception."""
        return self._val

    def unwrap_or(self, _x: _T) -> _T:
        """Return the wrapped value or give us x if it is Nothing."""
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

    def __rshift__(self, _f: Fn[[Any], Maybe[_R]]) -> Maybe[_R]:
        """Bind and apply f."""
        return Nothing

    def unwrap(self) -> Any:
        """Return the wrapped value or raise an exception."""
        raise IsNothing("tried to unwrap a Nothing value")

    def unwrap_or(self, _x: _T) -> _T:
        """Return the wrapped value or give us x if it is Nothing."""
        return _x


Nothing: Final = Nothing_()


class Fun(Generic[_T, _R]):
    """Wrap a callable _T -> Maybe[_R] so we can give it a type."""

    def __init__(self, f: Fn[[_T], Maybe[_R]]) -> None:
        """Wrap the callable f."""
        self._f = f

    def __call__(self, x: _T) -> Maybe[_R]:
        """Invoke the function."""
        return self._f(x)


class lift(Generic[_T, _R]):  # noqa: N801
    """Lift a callable _T -> _R to _T -> Maybe[_R]."""

    def __init__(self, f: Fn[[_T], _R]) -> None:
        """Wrap the callable f."""
        self._f = f

    def __call__(self, x: _T) -> Maybe[_R]:
        """Invoke the function."""
        res = self._f(x)
        return Nothing if res is None else Some(res)
