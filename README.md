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

This trick is, of course, more general than dealing with `None`. You can lift to other types as well if you need to, but that will have to be a topic for another day.

Just by lifting you can implement many algorithms that handles all common cases that do not involve `None` and let the lifting deal with special cases for you. At some point you need to get the result of the computation, of course, and there you need to know if you got `None` or not, but until then, you might not have to worry about it at all.

