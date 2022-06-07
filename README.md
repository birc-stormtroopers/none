# Dealing with data that isn't there

Frequently in life, and in programming, we have to deal with stuff that isn't there. In programming it could be asking for a subtree that isn't there, or asking for a value that isn't defined, and stuff like that. And there are multiple solutions around for dealing with it, in different programming languages. Exceptions is one such solution, found in many languages, but it is a rather blunt wepon in many cases. It is not every time that "nothing" means that something exceptional happened. If you keep traversing down a tree and never ever reach the end, something dodgy has happened; it is not an exceptional case that you eventually reach the end, it is the expected behaviour.

Expected nothingness, if we can call it that, is something we want, need, and have to deal with, one way or another. And even ignoring exceptions, there are multiple solutions found in different langauges. One of these, known from Python, C, Java and other languages is `null` or `None` in Rust or Python. A special value that indicates "nothingness".

The `None` in Python (which is completely equivalent to `null` in Java) might possibly be the worst solution ever thought of. At least the creator of Algol, one of the earliest semi-high-level languages thinks so:

    I call it my billion-dollar mistake…At that time, I was designing the first comprehensive
    type system for references in an object-oriented language. My goal was to ensure that all
    use of references should be absolutely safe, with checking performed automatically by the
    compiler. But I couldn’t resist the temptation to put in a null reference, simply because
    it was so easy to implement. This has led to innumerable errors, vulnerabilities, and
    system crashes, which have probably caused a billion dollars of pain and damage in the last
    forty years.
    – Tony Hoare, inventor of ALGOL W.

At least the idea is simple. Any type has a special value, `null` or `None`, that you can use to indicate that something isn't there. The problem is that *any variable of that type could be `null`!* It is a special case that is *always* there, and you need to check for it *all the time*--if you don't, one day you will try to use `null` as a real value and your program will crash.

The bastard means that we need to check for special cases *everywhere*. It makes code unreadable, and there is no compiler checks to help us if `null` is allowed everywhere.

On the other hand, it is hard to get away from `null`. We really do need it. But there are safer solutions. From a type perspective, we could distinguish between a type `T` that is not allowed to be `null` and then another type `Opt[T]` that includes all values in `T` and then `None`. This is how Python's type system works with `None`.

Python itself doesn't do static types so any variable can hold any value, and `None` is just another value, but the type checkers you can use with Python's type annotation distinguish between variables that can hold `None` and those that shouldn't. For example

```python
x: int
```

is a variable that can hold integers and 

```python
from typing import Optional

y: Optional[int]
```

declares a variable that can hold integers *and* `None`.

This is slightly better than allowing `None` for any type, but not prefect. If you have a variable with type `Optional[T]` you still need to deal with the special case `None` everywhere, and the type checker won't necessarily help you remember to check everywhere you ought to. Some places, yes, but it is not a bullet proof protection.

In `Rust`, the `Option<T>` type does the same thing, but it is safer because you really cannot treat an `Option<T>` as a `T` before you have explicitly checked that it isn't `None`. You get safety, but at the cost of making special case checks *everywhere*.

Today, we'll explore ways of dealing with `None` in a safe way, and in a way that help us eliminate many special cases, even beyond the special case of `None`.

## Lifting

The first approach is rather straightforward. I am going to assume that we can define a modified type, `Opt[T]`, for any type `T`, where `Opt[T]` is `T` + `None`. I'm implementing everything in Python, so it is simple there.

```python
from typing import (
    Optional as Opt,
)

def f(x: int) -> int:
    return x
def g(x: Opt[int]) -> Opt[int]:
    return x

f(12)    # Okay
f(None)  # Type error, None is not int
g(12)    # Okay
g(None)  # Okay, None is Opt[int]
```

Mapping types to some other, dependent, type, `T -> Opt[T]`, is sometimes called "lifting", and mapping functions `f: T -> S` to functions in the dependent type, `f': Opt[T] -> Opt[S]`, is called lifting as well, and is the trick to avoid dealing with special cases.

In most cases where we have a `None` we want to propagate it in calculations. It is like having a `NA` in `R`; any calculation you do on a value that is `NA` just ends up as `NA`. If we compute on something that isn't there, we should get a result that isn't there either.

If we have a function such as

```python
def f(x: int, y: int) -> int:
    return x + y
```

but either variable could be `None` because we get them from somewhere that isn't entirely reliable, we will likely crash at some point. You cannot add `None` to anything with incurring the wrath of the exception gods. But changing `f` to something that returns `None` if either input is `None` is entirely sensible.

```python
def f(x: Opt[int], y: Opt[int]) -> Opt[int]:
    return None if x is None or y is None else x + y
```

Now, we don't want to write functions like this--they are ugly--but if this is the behaviour we want, we can write a higher-order function to do the lift for us.

```python
from typing import (
    TypeVar,
    Callable as Fn,
    Optional as Opt,
    Any,
)

from functools import wraps

_R = TypeVar('_R')

def lift(f: Fn[..., Opt[_R]]) -> Fn[..., Opt[_R]]:
    """Lift a generic function."""
    @wraps(f)
    def w(*args: Any, **kwargs: Any) -> Opt[_R]:
        if None in args or None in kwargs.values():
            return None
        return f(*args, **kwargs)
    return w
```

The `lift` function will take any function and wrap it to a function that returns `None` if any argument is `None` and otherwise invoke the original function. The type annotation is a bit dodgy, because it throws away the type information of the arguments, and Python doesn't have a nice way of dealing with that, but you can overload `lift` and get proper type checking that way. See `optional.py`.

With this fellow, we can write functions that ignore `None`, and still deal with them correctly. We can wrap functions when we need them

```python
f(None, 12)        # type error
lift(f)(None, 12)  # quite okay
```

or we can use decorators to wrap functions

```python
@lift
def f(x: int, y: int) -> int:
    return x + y

f(None, 12) # fine, wrapped f deals with None
```

But see below for issues if `f` is a generic function.

This trick is, of course, more general than dealing with `None`. You can lift to other types as well if you need to, but that will have to be a topic for another day.

Just by lifting you can implement many algorithms that handles all common cases that do not involve `None` and let the lifting deal with special cases for you. At some point you need to get the result of the computation, of course, and there you need to know if you got `None` or not, but until then, you might not have to worry about it at all.

A word of warning here, though. And this is a Python specific thing, because Python's type checking is still somewhat experimental. Very interesting, but weird at times.

You might think that something like

```python
@lift
def f(x: _T) -> _T:
    return x
```

should work and give you a function `Opt[_T] -> Opt[_T]`--I certainly think that--but it doesn't.

If you use the [`pyre` type checker](https://pyre-check.org/play?input=from%20typing%20import%20(%0A%20%20%20%20TypeVar%2C%0A%20%20%20%20Callable%20as%20Fn%2C%0A%20%20%20%20Optional%20as%20Opt%2C%0A%20%20%20%20Any%2C%0A%20%20%20%20overload%0A)%0A%0Afrom%20functools%20import%20wraps%0A%0A_T%20%3D%20TypeVar(%27_T%27)%0A_R%20%3D%20TypeVar(%27_R%27)%0A%0A_1%20%3D%20TypeVar(%27_1%27)%0A_2%20%3D%20TypeVar(%27_2%27)%0A_3%20%3D%20TypeVar(%27_3%27)%0A_4%20%3D%20TypeVar(%27_4%27)%0A%0A%0A%40overload%0Adef%20lift(f%3A%20Fn%5B%5B_1%5D%2C%20Opt%5B_R%5D%5D)%20-%3E%20Fn%5B%5BOpt%5B_1%5D%5D%2C%20Opt%5B_R%5D%5D%3A%0A%20%20%20%20%22%22%22Lift%20function%20f.%22%22%22%0A%20%20%20%20...%0A%0A%0A%40overload%0Adef%20lift(f%3A%20Fn%5B%5B_1%2C%20_2%5D%2C%20Opt%5B_R%5D%5D)%20-%3E%20Fn%5B%5BOpt%5B_1%5D%2C%20Opt%5B_2%5D%5D%2C%20Opt%5B_R%5D%5D%3A%0A%20%20%20%20%22%22%22Lift%20function%20f.%22%22%22%0A%20%20%20%20...%0A%0A%0A%40overload%0Adef%20lift(f%3A%20Fn%5B%5B_1%2C%20_2%2C%20_3%5D%2C%20Opt%5B_R%5D%5D)%20%5C%0A%20%20%20%20%20%20%20%20-%3E%20Fn%5B%5BOpt%5B_1%5D%2C%20Opt%5B_2%5D%2C%20Opt%5B_3%5D%5D%2C%20Opt%5B_R%5D%5D%3A%0A%20%20%20%20%22%22%22Lift%20function%20f.%22%22%22%0A%20%20%20%20...%0A%0A%0A%40overload%0Adef%20lift(f%3A%20Fn%5B%5B_1%2C%20_2%2C%20_3%2C%20_4%5D%2C%20Opt%5B_R%5D%5D)%20%5C%0A%20%20%20%20%20%20%20%20-%3E%20Fn%5B%5BOpt%5B_1%5D%2C%20Opt%5B_2%5D%2C%20Opt%5B_3%5D%2C%20Opt%5B_4%5D%5D%2C%20Opt%5B_R%5D%5D%3A%0A%20%20%20%20%22%22%22Lift%20function%20f.%22%22%22%0A%20%20%20%20...%0A%0A%0Adef%20lift(f%3A%20Fn%5B...%2C%20Opt%5B_R%5D%5D)%20-%3E%20Fn%5B...%2C%20Opt%5B_R%5D%5D%3A%0A%20%20%20%20%22%22%22Lift%20a%20generic%20function.%22%22%22%0A%20%20%20%20%40wraps(f)%0A%20%20%20%20def%20w(*args%3A%20Any%2C%20**kwargs%3A%20Any)%20-%3E%20Opt%5B_R%5D%3A%0A%20%20%20%20%20%20%20%20if%20None%20in%20args%20or%20None%20in%20kwargs.values()%3A%0A%20%20%20%20%20%20%20%20%20%20%20%20return%20None%0A%20%20%20%20%20%20%20%20return%20f(*args%2C%20**kwargs)%0A%20%20%20%20return%20w%0A%0A%0A%40lift%0Adef%20f(x%3A%20_T)%20-%3E%20_T%3A%0A%20%20%20%20return%20x%0A%0Areveal_type(f)%0Af(12)), it is really weird. It thinks it should be a function `None -> None` and for the death of me I cannot work out why. But I don't use that checker anyway, as it doesn't implement all of the newer type features anyway.

The [`mypy`](https://mypy-play.net/?mypy=latest&python=3.10&gist=a8f6d8fef8bea466d29e95e75a133780) and `pyright` checkes will tell you that you have a function `Opt[_T'-1] -> Opt[_T'-1]` (mypy) or `(_T@f | None) -> (_T@f | None)` (pyright) where the `_T'-1` or `_T@f` is a bound type, bound to the type when you called `lift`. There isn't such a type, the function `f` was generic, so the effect of this is that we have a function with a type that will never match anything else. A completely useless function.

I think this is a bug, and I have reported it as such, but there is some disagreement on whether this is the intended behaviour or not.

In any case, it is only a problem if you lift a function with generic type. If you use a concrete type, or put the lift in a function where the generic parameters will be know, you don't have a problem. This will work:

```python
def apply(x: _T, f: Fn[[_T], _T]) -> Opt[_T]:
    ff = lift(f)  # Lift's ff, but here _T will be bound to apply's _T
    return ff(x)  # This will be Opt[_T] for the bound _T

apply(12, f)      # An Opt[int] because x is int
apply("foo", f)   # An Opt[str] because x is str
```

I have tried all kinds of trickery to implement generic lifting, but to no avail. I don't think it is currently possible. You just have to defer lifting until types are known.

Anyway, moving on...

If we have lifted functions, we can write functions that do not have to deal with `None` and automatically handle when we get a `None` anyway. (This is also a technique that works for more general error handling, but no need to go into that here).

There are some drawbacks, though. This lifting stuff only works if you lift every function that needs to deal with a `None`, and notation wise, that might be cumbersome. Some languages do everything with functions, and you won't notice it there, but with something like Python you quickly get something that looks very odd.

Consider computing the roots of a quadratic equation, $ax^2 + bx + c = 0$. The two real solutions, if they exist, are 

$$ x = {-b \pm \sqrt{b^2-4ac} \over 2a} $$

but you can get into trouble two places here. If $(b^2-4ac) < 0$ you can't take the square root (at least not in the reals) and if $a=0$ you can't divide by $2a$. Those are failure points and we can translate them into `None`, so it looks like something our new lifting magic can deal with. It can, but as I warned you, it might look a bit odd.

The problem is that the errors appear in the middle of the expression and we need to propagate them out from there, but our `lift` magic can only handle changing function parameters, so we need to move the expressions there. One way is straightforward: make `sqrt()` return a `None` rather than cast an exception

```python
def catch_to_none(f: Fn[_P, _R]) -> Fn[_P, Opt[_R]]:
    """Wrap a function so it returns None instead of an exception."""
    @wraps(f)
    def w(*args: _P.args, **kwargs: _P.kwargs) -> Opt[_R]:
        try:
            return f(*args, **kwargs)
        except Exception:
            return None
    return w

@catch_to_none  # math.sqrt() might throw ValueError
def sqrt(x: float) -> float:
    """Return sqrt of x or None if not defined."""
    return math.sqrt(x)
```

then compute the square root first, put it into a function that handles if the result was `None`, and make sure that function translates a division by zero into `None`:

```python
def roots(a: float, b: float, c: float) -> Opt[tuple[float, float]]:
    """Get the roots of the quadratic equation ax**2 + bx + c."""
    @catch_to_none  # We could divide by zero
    @lift           # sq could be None
    def _roots(sq: float) -> tuple[float, float]:
        return (-b - sq) / (2*a), (-b + sq) / (2*a)

    return _roots(sqrt(b**2 - 4*a*c))
```

Here, the lifting didn't do much for us. We could just have caught the exception in the first place...

```python
@catch_to_none
def roots(a: float, b: float, c: float) -> tuple[float, float]:
    """Get the roots of the quadratic equation ax**2 + bx + c."""
    sq = math.sqrt(b**2 - 4*a*c)
    return (-b - sq) / (2*a), (-b + sq) / (2*a)
```

This is partly because we are in a situation where we get exceptions if something goes wrong, and partly because we always want exceptions to become `None`, so it is a little misleading, but does tell us that lifting might not be the thing for us here.

If you want a proper lifting solution, you need all the expressions to handle `None`, so we don't handle errors through exceptions, but that means that we have to lift all the operators.

```python
@lift
def neg(x: float) -> float:
    """Return -x."""
    # can't use operator.neg bcs type binding
    return x


sub = lift(operator.sub)
add = lift(operator.add)
mul = lift(operator.mul)


@lift
def div(a: float, b: float) -> Opt[float]:
    """Return a/b or None if b is zero."""
    return None if b == 0 else a / b


@catch_to_none  # math.sqrt() might throw ValueError
def sqrt(x: float) -> float:
    """Return sqrt of x or None if not defined."""
    return math.sqrt(x)


def roots(a: float, b: float, c: float) -> tuple[Opt[float], Opt[float]]:
    """Get the roots of the quadratic equation ax**2 + bx + c."""
    sq = sqrt(b**2 - 4*a*c) # didn't bother with lifted functions in arg here
    return div(sub(neg(b), sq), mul(2, a)), div(add(neg(b), sq), mul(2, a))
```

Some languages already use functions for operators, and then it wouldn't look at odd, but it does here. We can lift operators, though, but only through methods, and we will look at a solution that enables that in the next section.

Right now, it might look like the lifting is completely useless, but I don't think it is. It just isn't the right solution for evaluating expressions, because we are used to operators for that, and we cannot easily lift operators. For arithmetic, that is a big deal, but for many algorithms it isn't.

Consider swapping with the smallest child in a binary heap. There you need to get the two children of a node, and one or both might be `None`. So you have special cases there, that you would have to check for. Those cases follow you into comparing the node with the children to find the smallest child, and perhaps even into the swap. You can hide all of this if looking up a value in an array would give you `None` instead throwing an exception, and then having a less-than function, `lt`, that is only true for `lt(x,y)` if both `x` and `y` are non-None and `x < y`.

```python
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
```

Using `lt(x,y)` instead of `x < y` is not too much to pay to avoid checking if indices are out of bounds or if values are `None`.

Of course, even if you are using something like `lift`, it doesn't mean that you shouldn't use all the other features in the langauge. You can combine optional types with other features. There is nothing wrong with exceptions, for example, and you can use them together with `Opt[T]` values with something like this:

```python
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
```

Whenever you ahve an `Opt[T]` value, the type checker should warn you if you use it without checking if it is `None`, but if you use `unwrap` you force the type to be `T` and get an exception if you are wrong. You can use that to handle errors if you want. Allow your variables to hold `Opt[T]` and `unwrap()` every time you use them. Then use a `try - except` block to catch if something went wrong.

You could, for example, write a function that folds a function over `Opt[T]` values, skipping `None` output but returning `None` if the function ever produces a `None`.

```python
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
```

This combines a form of lifting with `unwrap()` and catching `IsNone` to implement the behaviour we want.

We could use this `fold` combined with a `min` to get the smallest child of a node in a binary heap, and use that to swap.

```python
def get(x: list[_T], i: int) -> Opt[tuple[_T, int]]:
    """Get value at index i if possible."""
    try:
        return (x[i], i)
    except IndexError:
        return None


def swap_min_child(x: list[Ord], p: int) -> None:
    """Swap node p with its smallest child."""
    child = fold(min, get(x, 2*p + 1), get(x, 2*p + 2))
    if lt(child, get(x, p)):
        _, c = unwrap(child)  # If child < parent it can't be None
        x[p], x[c] = x[c], x[p]
```

or

```python
def swap_min_child(x: list[Ord], p: int) -> None:
    """Swap node p with its smallest child."""
    child = fold(min, get(x, 2*p + 1), get(x, 2*p + 2))
    try:
        v, c = unwrap(child)
        if v < x[p]:
            x[p], x[c] = x[c], x[p]

    except IsNone:
        pass
```

using `unwrap()` and the exception once again.



## The `Maybe` monad

When we are lifting, we are modifying functions to deal with `None`, but we are not touching the variables so we cannot change operators and such. This is somewhat because of how Python handles `None`, if it was a special type as in Rust rather than a tag-on `None` that goes into ever type, we might be able to do something. But as it is, `None` is in any type and we cannot easily wrap variables with extra type information. We can, however, define new types that captures "a type `T` and `None`".

One approach to this is the `Maybe` monad. A monad is an idea from category theory that is used extensively in pure functional languages like Haskell. It is an abstract concept with many uses, from I/O to handling optinal values like we do here.

A monad consists of an extended type `M[T]` (The monad `M` over type `T`) and two functions:

The function `unit` or `return`

```
    unit: T -> M[T]
```

that sends a T value into the monad, and the function `bind` (I don't know why it has this name, it applies) that applies a function on a monad value

```
    bind: M[T] -> (T -> M[S]) -> M[S]
```

it takes a `M[T]` value, `a` and a function that sends a `T` value to `M[S]`, `f`, and then it gives us `f(a')` if `a'` is a `T` value underlying the `a` value in `M[T]` and something else in `M[S]` otherwise.

To make it more concrete, let's say we have a type `T` and we want to handle something like `T` + `None`. We call the monad `Maybe` and it can have two types of values, `Some(a)` for values `a` from `T`, or `Nothing`.

We can send `T` values into `Maybe[T]` with

```python
def unit(a: T) -> Maybe[T]:
    return Some(a)
```

and if we want to apply (or bind) a function we have

```python
def bind(a: Maybe[T], f: Fn[[T], Maybe[S]]) -> Maybe[S]:
    match a:
        case Nothing:
            return Nothing
        case Some(a_):
            return f(a_)
```

The `bind()` function is usually implemented as an infix
operator, `>>=`, so we would apply it as

```haskell
    a >>= lambda a_: Some(...)
```

or something to that effect. We can't use `>>=` in Python
because that is only allowed as a statement, but we could
use `>>`.

You can implement it with a single class that checks what it wraps as a value, but I will implement an abstract `Maybe` class and two sub-classes, one for `Some()` and one for `Nothing`. The `Some()` constructor will work as `unit` and I make the `Nothing` class a singleton so there is only ever one `Nothing`.

```python
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

    @property
    @abstractmethod
    def is_some(self) -> bool:
        """Return true if we hold a value, otherwise false."""
        ...

    @property
    @abstractmethod
    def is_nothing(self) -> bool:
        """Return true if we do not hold a value, otherwise false."""
        ...

class Some(Maybe[_T]):
    """Objects containing values."""

    _val: _T

    def __init__(self, val: _T) -> None:
        """Create a new monadic value."""
        self._val = val

    def __repr__(self) -> str:
        """Get repr for Maybe[_T]."""
        return f"Some({self._val})"

    def __bool__(self) -> bool:
        """Return true if val is true."""
        return bool(self._val)

    def __rshift__(self, f: Fn[[_T], Maybe[_R]]) -> Maybe[_R]:
        """Bind and apply f."""
        return f(self._val)

    def unwrap(self) -> _T:
        """Return the wrapped value or raise an exception."""
        return self._val

    @property
    def is_some(self) -> bool:
        """Return true if we hold a value, otherwise false."""
        return True

    @property
    def is_nothing(self) -> bool:
        """Return true if we do not hold a value, otherwise false."""
        return False


class IsNothing(Exception):
    """Exception raised if we try to get the value of Nothing."""

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

    def __rshift__(self, _f: Fn[[_T], Maybe[_R]]) -> Maybe[_R]:
        """Bind and apply f."""
        return Nothing

    def unwrap(self) -> _T:
        """Return the wrapped value or raise an exception."""
        raise IsNothing("tried to unwrap a Nothing value")

    @property
    def is_some(self) -> bool:
        """Return true if we hold a value, otherwise false."""
        return False

    @property
    def is_nothing(self) -> bool:
        """Return true if we do not hold a value, otherwise false."""
        return True


Nothing = Nothing_() # the Nothing object
```

The idea with a monad is that you can string together a number of operations with the bind operator, and the monad takes care of handling additional information, like whether you have a `Nothing` or not. (It is, of course, much more general).

```python
x = Some(1) >> (lambda a: Some(2*a)) >> (lambda a: Some(-a))
print(x)  # Some(-2)

y = Nothing >> (lambda a: Some(2*a)) >> (lambda a: Some(-a))
print(y)  # Nothing
```

Here, again, we are going to run into a problem with Python's type checkers--the type system isn't really grown up yet. The `lambda` expressions aren't typed, so these expressions are giving us `Maybe[Unknown]` types, which isn't type safe. To type the expressions we can wrap them in a class, where we can make the types explicit when the type checker cannot infer them.

```python
class Fun(Generic[_T, _R]):
    """Wrap a callable _T -> Maybe[_R] so we can give it a type."""

    def __init__(self, f: Fn[[_T], Maybe[_R]]) -> None:
        """Wrap the callable f."""
        self._f = f

    def __call__(self, x: _T) -> Maybe[_R]:
        """Invoke the function."""
        return self._f(x)
```

Then we can give our lambda expressions types

```python
x = Some(12) >> \
    Fun[int, int](lambda a: Some(2*a)) >> \
    Fun[int, int](lambda a: Some(-a))
print(x)  # Some(-24), Maybe[int]
```

We can still use plain functions if their types are know, though:

```python
def f(a: int) -> Maybe[int]:
    return Some(2 * a)
def neg(a: int) -> Maybe[int]:
    return Some(-a)

x = Some(12) >> f >> neg
print(x)  # Some(-24), Maybe[int]
```

We could also combine such a function with a lift from `T -> R` to `T -> Maybe[R]` that we could also use as a decorator or for wrapping operators:

```python
class lift(Generic[_T, _R]):
    """Lift a callable _T -> _R to _T -> Maybe[_R]."""

    def __init__(self, f: Fn[[_T], _R]) -> None:
        """Wrap the callable f."""
        self._f = f

    def __call__(self, x: _T) -> Maybe[_R]:
        """Invoke the function."""
        res = self._f(x)
        return Nothing if res is None else Some(res)

# lifting and wrapping lambdas
x = Some(12) >> \
    lift[int, int](lambda a: 2*a) >> \
    lift[int, int](lambda a: -a)
print(x)  # Some(-24), Maybe[int]

# lifting a function as a decorator
@lift
def f(a: int) -> int:
    return 2 * a

# operator.neg is lifted to return a Maybe
x = Some(12) >> f >> lift(operator.neg)
print(x)  # Some(-24), Maybe[int]
```

A pipeline like this is quite convinient when you have data flowing through a sequence of function calls, that doesn't happen that often outside of data science projects. Usually, we have functions that take more than one argument, and here the notation gets a little cumbersome. You will have to curry the computation and bind functions inside other functions. Here is how you add two numbers with a plain monad:

```python
# (x, y) -> x + y === x -> y -> x+y
x = Some(12)
y = Some(30)
z: Maybe[int] =  \
    x >> (lambda a:  # a is the value in x
          y >> (lambda b:  # b is the value in y
                Some(a+b)))  # return their sum
print(z)  # Maybe[42], Maybe[int]
```

You can get used to code like that. It looks a little better without the comments, actually

```python
z: Maybe[int] = x >> (lambda a: y >> (lambda b: Some(a+b)))
```

but it doesn't look like natural Python code, and it isn't easy to read in languages where this kind of code comes natural either. 

Haskell has built-in syntactic sugar that lets  you unwrap a sequence of monads and then do a computation, but we don't have that in Python. That won't stop us from implementing it, though; we are just a little limited in the kind of syntacs we can define. But we can get something that looks like this:

```python
z = Maybe.do(a - b 
             for a in Some(44)
             for b in Some(2))
```

where you can unwrap any number of monads by adding more `for ... in ...` lines. Something like this is called a generator expression, and we can write a function that takes one and evaluates it. We need two parts, the part that evaluates the generator expression, and the part that lets us iterate over a monad. Both are quite simple:

```python
class Maybe(Generic[_T], ABC):
    """Maybe monad over T."""

    ...

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
        res = next(expr)
        return res if isinstance(res, Maybe) else Some(res)
```

The expressions we have in mind will iterate over one value per monad, so the generator expression should only produce a single value. We get that when we ask for `next(expr)`. Then we just have to wrap it. There are times where it is convinient to let the expression return a `Maybe`, though, for example to handle error cases (when we cannot avoid that), so we check if the return value is a `Maybe`, in which case we simply return it, and if it isn't, we lift it with `Some(res)`.

If there is a `Nothing` in any of the input monads, then unwrapping will raise `IsNothing`, which we catch and turn into a `Nothing`.

With the `do` operator we can get close to the syntax we would use if we didn't have any `Nothing` at all, and were just writing Python code. Not quite there, but close enough that it might be worth it, just to not worry about special cases.

This is true even for arithmetic heavy code. The roots of quadratic equations code illustrates this:

```python
def inv(x: float) -> Maybe[float]:
    """Return 1/x if x != 0."""
    return Nothing if x == 0 else Some(1/x)


def sqrt(x: float) -> Maybe[float]:
    """Compute the square root if x >= 0."""
    return Some(math.sqrt(x)) if x >= 0 else Nothing


def roots(a: float, b: float, c: float) -> Maybe[tuple[float, float]]:
    """Get the roots of the quadratic equation ax**2 + bx + c."""
    return Maybe.do(
        ((-b - sq) / i, (-b + sq) / i)
        for i in inv(2 * a)
        for sq in sqrt(b**2 - 4*a*c)
    )
```

We still have to extract the problematic bits, inverting `2*a` and taking the square root, because these functions do not know about monads, but the expression in the `do` expression are reasonably readable now.

Since we are wrapping values in a new class, however, we can now also define operators on them. This is a bit cumbersome if you want type checking, and a bit unreliable as well. You can easily write a wrapping function that generates the functions you need, but to annotate them with type information, you need to define the operators manually. At least I haven't found a type checker that can handle other solutions. Still, it is doable.

You want to use protocols to specify which underlying types should support a type. If you just define, say `__add__` on `Maybe[_T]`, you tell the type checkers that *any* `_T` will have a plus operator, and that clearly isn't what you want. But if you define a protocol for, say, arithmetic types

```python
class Arithmetic(Protocol):
    """Types that support < comparison."""

    def __neg__(self: Arith, /) -> Arith:
        """-self."""
        ...

    def __add__(self: Arith, other: Arith, /) -> Arith:
        """Add self and other."""
        ...

    def __sub__(self: Arith, other: Arith, /) -> Arith:
        """Subtract other from self."""
        ...

    def __mul__(self: Arith, other: Arith, /) -> Arith:
        """Multiply self and other."""
        ...

    def __pow__(self: Arith, other: Arith, /) -> Arith:
        """Raise self to other."""
        ...

    def __truediv__(self: Arith, other: Arith, /) -> Arith:
        """Divide self by other."""
        ...

    def __floordiv__(self: Arith, other: Arith, /) -> Arith:
        """Divide self by other."""
        ...

Arith = TypeVar('Arith', bound=Arithmetic)
```

you can define that `Maybe[_T]` should support these opoerators when `_T` supports them:

```python

class Maybe(Generic[_T], ABC):
    """Maybe monad over T."""

    ...

    def __lt__(self: Maybe[Ord], other: Maybe[Ord]) -> Maybe[bool]:
        """Test less than, if _T is Ord."""
        return Maybe.do(a < b for a in self for b in other)

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
```

It *is* annoying to explicitly define all of these, but you only need to do it once.

Unfortunately, and to no surprise, the support for this is dodgy. The `mypy` checker supports this up to a point, it allows you to constraint most arguments with protocols, but it doesn't seem to support constrained `self` types, unless it is a concrete type. It doesn't handle protocols like this, and will think that if we define `__add__` for a `Maybe`, then we support it for any `Maybe[_T]` whether `_T` supports `+` or not. The `pyright` gets it right, though.

Anyway, with the operators in `Maybe`, we can implement the `roots` function like this:

```python
def sqrt(x: Maybe[float]) -> Maybe[float]:
    """Compute the square root if x >= 0."""
    return Maybe.do(
        Some(math.sqrt(a)) if a >= 0 else Nothing
        for a in x
    )


def roots(a_: float, b_: float, c_: float
          ) -> tuple[Maybe[float], Maybe[float]]:
    """Get the roots of the quadratic equation ax**2 + bx + c."""
    a, b, c = Some(a_), Some(b_), Some(c_)
    sq = sqrt(b**Some(2.0) - Some(4.0)*a*c)
    return ((-b - sq) / (Some(2.0)*a), (-b + sq) / (Some(2.0)*a))
```

We are getting closer to how we would write the code in plain Python without any error handling. The `Some(-)` wrapping is the only thing that distinguishes this from working with plain `float`, and if you work at little more at the operators you can make them accept more types. You can't dispatch on type, so you need to explicitly check the types, but that is all you would need. I'm just too lazy for that right now.

Wrapping back to the binomial heap for another example of using a `Maybe`, we could wrap sequences so they could work with `Maybe`:

```python
class MList(Generic[_T]):
    """Wrapping a sequence so it returns Maybe."""

    _seq: MutableSequence[_T]

    def __init__(self, seq: MutableSequence[_T]) -> None:
        """Wrap seq in an MList."""
        self._seq = seq

    def __getitem__(self, i: int) -> Maybe[_T]:
        """Return self[i] if possible."""
        return Some(self._seq[i]) \
            if 0 <= i < len(self._seq) \
            else Nothing

    def __setitem__(self, i: int, val: Maybe[_T]) -> None:
        """Set self[i] to val if Some and possible."""
        if 0 <= i < len(self._seq):
            try:
                self._seq[i] = val.unwrap()
            except IsNothing:
                pass
```

and then implement the swap code without explicitly dealing with special cases at all:

```python
def swap_down(p: int, x: MList[Ord]) -> None:
    """Swap p down if a child is smaller."""
    me, left, right = x[p], x[2*p + 1], x[2*p + 2]
    if left < me and not right < left:
        x[p], x[2*p + 1] = x[2*p + 1], x[p]
    if right < me and not left < right:
        x[p], x[2*p + 2] = x[2*p + 2], x[p]
```

The weird expression `right < me and not left < right` with a `not ... < ...` is not as natural as `right < me and right < left`, but it is necessary here. Our lifted `<` will return `Nothing` which evaluates to `False` whenever either element is `Nothing` and that is an issue.

We have gotten rid of handling special cases, and we are even doing it type-safe (with the right checker), but at sizable cost. If boolean expressions don't mean what they usually do, it is *very* easy to make mistakes. We probably don't want that.

It makes sense to lift code from `T x S -> R` to `Maybe[T] x Maybe[S] -> Maybe[R]` in many cases, but not when the domain `R` is something we could confuse for `Nothing`.

We don't want `Maybe` to function as a boolean, so let's fix that. I don't think we can remove `__bool__()` from an object to tell the type checker that it cannot use an object as a boolean. All objects can be used as type values. But we can raise a runtime exception if it happens.

```python
    def __bool__(self) -> bool:
        """Make sure we don't use a Maybe as a bool."""
        assert False, "A Maybe is not a truth-value."
        return False
```

Frustratingly, the type checker doesn't complain that we *do* use `Maybe` as a boolean, but the `swap_down()` function will crash.

Let's go back and check what the problem is. In the expression, we want `left < me` to be true if both `left` and `me` have values and `left.unwrap() < me.unwrap()`. We want `left < right` to be true if `right` is `Nothing` or if `left.unwrap() < right.unwrap()`. We are trying to give `<` different meanings depending on where we use it, and that is the problem here. We need to take control over `Nothing`.

We can get this control with an alternative `unwrap()` function, `unwrap_or()`, that either gives us the wrapped value or one we provide.

```python
class Maybe(Generic[_T], ABC):
    """Maybe monad over T."""

    ...

    def unwrap_or(self, _x: _T) -> _T:
        """Return the wrapped value or give us x if it is Nothing."""
        ...


class Some(Maybe[_T]):
    """Objects containing values."""

    ...

    def unwrap_or(self, _x: _T) -> _T:
        """Return the wrapped value or give us x if it is Nothing."""
        return self._val

class Nothing_(Maybe[Any]):
    """Nothing to see here."""

    ...

    def unwrap_or(self, _x: _T) -> _T:
        """Return the wrapped value or give us x if it is Nothing."""
        return _x
```

If we want `left < me and left < right` to be `True` if `left` and `me` exists and `left.unwrap() < me.unwrap()`, then `(left < me).unwrap_or(False)` will do the trick. If we want `left < right` to be true, when we know that `left` holds a value, if either `right` is `Nothing` or both have a value where `left.unwrap() < right.unwrap()`, then `(left < right).unwrap_or(True)` will do the trick.

```python
def swap_down(p: int, x: MList[Ord]) -> None:
    """Swap p down if a child is smaller."""
    me, left, right = x[p], x[2*p + 1], x[2*p + 2]
    if (left < me).unwrap_or(False) and (left < right).unwrap_or(True):
        x[p], x[2*p + 1] = x[2*p + 1], x[p]
    if (right < me).unwrap_or(False) and (right < left).unwrap_or(True):
        x[p], x[2*p + 2] = x[2*p + 2], x[p]
```

We have moved a little away from the error-checking-free code again, but that is better than having expressions that do not mean what they appear to mean. And sometimes we simply cannot completely hide that we are working with a `Maybe`-monad completely, especially when we need to treat `Nothing` differently.

Related to `unwrap_or()` we might want expressions where we stay in the `Maybe` domain, but want to have an alternative to `Nothing`. A good name for such a function would be `or()` but that is a keyword in Python. So let's just use the operator `|` otherwise used for bit-wise or:

```python
    # Maybe
    def __or__(self, other: Maybe[_T]) -> Maybe[_T]:
        """Return self if it is Some, otherwise other."""
        ...

    # Some
    def __or__(self, other: Maybe[_T]) -> Maybe[_T]:
        """Return self if it is Some, otherwise other."""
        return self._val

    # Nothing
    def __or__(self, other: Maybe[_T]) -> Maybe[_T]:
        """Return self if it is Some, otherwise other."""
        return other
```

We can use this for a "maybe min" function that gives us the smalleset of two values, or the non-`Nothing` value if there is one, or `Nothing` if that is all the input is.

```python
def maybe_min(x: Maybe[Ord], y: Maybe[Ord]) -> Maybe[Ord]:
    """
    Get min of x and y.

    If one of the two is Nothing, we get the other.
    """
    # If both arguments are Some, then we get the smallest
    return Maybe.do(
        b if b < a else a
        for a in x for b in y
    ) | x | y
    # otherwise we pick the first non-Nothing or we end up with Nothing
```

With a little bit of rewriting we can get another version of `swap_down()`--this time one that loops until we are done swapping--that looks like this:

```python
_1 = TypeVar('_1')
_2 = TypeVar('_2')


def pair(first: Maybe[_1], second: Maybe[_2]) -> Maybe[tuple[_1, _2]]:
    """Turn a pair of Maybe into a Maybe pair."""
    return Maybe.do((a, b) for a in first for b in second)


def get_index(x: MList[_T], i: int) -> Maybe[tuple[_T, int]]:
    """Get an array value together with its index."""
    return pair(x[i], Some(i))


def maybe_min(x: Maybe[Ord], y: Maybe[Ord]) -> Maybe[Ord]:
    """
    Get min of x and y.

    If one of the two is Nothing, we get the other.
    """
    # If both arguments are Some, then we get the smallest
    return Maybe.do(
        b if b < a else a
        for a in x for b in y
    ) | x | y
    # otherwise we pick the first non-Nothing or we end up with Nothing


def swap(x: MList[Ord], i: int, j: int) -> int:
    """Swap indices i and j, return new index for i."""
    x[i], x[j] = x[j], x[i]
    return j


def swap_down(p: int, x: MList[Ord]) -> None:
    """Swap p down if a child is smaller."""
    i = Some(p)
    while i.is_some:
        i = Maybe.do(
            # Swap parent and child if child is smaller, return the
            # index we swap to if we swap, so we can continue from there.
            # If we don't swap, return Nothing.
            swap(x, my_idx, child_idx) if child_val < my_val else Nothing

            for my_val, my_idx in get_index(x, p)
            for child_val, child_idx in maybe_min(get_index(x, 2*p + 1),
                                                  get_index(x, 2*p + 2))
        )
```

It works by wrapping up into a pair the index and value of an array. With the value first, we can get the smaller value, and remember its index, by taking `min`, or in this case `maybe_min` since the value at an index might not exist. Then, working with the `Maybe` monad, we can get the current index and the two child indices, get the smallest of the children, and swap the two if the child is smaller than the parent.

There are some limitations in what code we can write in a `do` operation, because it has to be a generator expression, so the actual swap has to go into a separate function, but otherwise I think the code is reasonably easy to read.

It is a bit backwards compared to usual Python code, when we assign the variables after the expression in the `do` statement, but with a little practise, you can get used to it. If you are familiar with some functional languages, it doesn't look quite as odd; there you often have constructions for defining variables after the result of a function.

But the readability isn't the main point here. We want something where the type explicitly encodes the special cases--in this case that we might index something that doesn't exit--and that will hide away the various special cases because of it. Here, either child could be outside of the array, so there are two children that we would need to deal with special cases for. This is now entirely hidden in the `MList` class and the `pairs` function. The `maybe_min` function also needs to consider the special cases, because it can't just propagate `Nothing` but must choose what to do if one of the input are `Nothing` but the other isn't. This, however, is something you can easily write a wrapper for, similar to `lift`. Then an explicit wrap, or a decorator, will hide this from you as well.

You can rarely get rid of *all* references to special cases, and we didn't achieve that here either, but if you can move them away from the main algorithm you have made a substantial improvement. Wrapping either functions, lifting them so you can write in an exception-less domain and then handle exceptional cases automatically, or wrapping data, in something like a Maybe monad, so exceptional cases are again handled automatically or hidden away in a few functions, can go a long way to writing more readable and maintainable code, and reducing the risk of missing handling the exceptional cases that do remain.

