"""Testing type constructions."""

from typing import (
    TypeVar, Generic,
)
from collections.abc import (
    MutableSequence
)
from maybe import (
    Maybe, Some, Nothing, IsNothing
)
from protocols import (
    Ord,
)

_T = TypeVar("_T")


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

    def __repr__(self) -> str:
        """Representation."""
        return repr(self._seq)


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


x = MList([3, 1, 2, 0, 4, 6, 1, 1, 2, 1, 0])
print(x)
swap_down(0, x)
