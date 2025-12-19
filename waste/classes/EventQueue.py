from __future__ import annotations

import logging
from heapq import heappop, heappush
from itertools import count
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from .Event import Event

logger = logging.getLogger(__name__)


class EventQueue:
    """Simple event queue that efficiently manages events in order of time."""

    def __init__(self):
        self._events = []
        self._counter = count(0)

    def __len__(self) -> int:
        return len(self._events)

    def push(self, event: Event):
        logger.debug(f"Adding event {event} to the queue at t = {event.time}.")

        tiebreaker = next(self._counter)
        heappush(self._events, (event.time, tiebreaker, event))

    def pop(self) -> Event:
        *_, event = heappop(self._events)
        return event

    def __iter__(self) -> Iterator[Event]:
        return (event for *_, event in self._events)
