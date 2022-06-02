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


