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


def swap_down(p: int, x: MList[Ord]) -> None:
    """Swap p down if a child is smaller."""
    me, left, right = x[p], x[2*p + 1], x[2*p + 2]
    if (left < me).unwrap_or(False) and (left < right).unwrap_or(True):
        x[p], x[2*p + 1] = x[2*p + 1], x[p]
    if (right < me).unwrap_or(False) and (right < left).unwrap_or(True):
        x[p], x[2*p + 2] = x[2*p + 2], x[p]


x = MList([3, 1, 2, 4, 6])
swap_down(0, x)
