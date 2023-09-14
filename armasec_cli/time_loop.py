from __future__ import annotations

from dataclasses import dataclass

import pendulum
from rich.progress import Progress

from armasec_cli.exceptions import ArmasecCliError


@dataclass
class Tick:
    counter: int
    elapsed: pendulum.Duration
    total_elapsed: pendulum.Duration


class TimeLoop:
    advent: pendulum.DateTime | None
    moment: pendulum.DateTime | None
    last_moment: pendulum.DateTime | None
    counter: int
    progress: Progress | None
    duration: pendulum.Duration
    message: str
    color: str

    def __init__(
        self,
        duration: pendulum.Duration | int,
        message: str = "Processing",
        color: str = "green",
    ):
        self.moment = None
        self.last_moment = None
        self.counter = 0
        self.progress = None
        if isinstance(duration, int):
            ArmasecCliError.require_condition(
                duration > 0,
                "The duration must be a positive integer",
            )
            self.duration = pendulum.duration(seconds=duration)
        else:
            self.duration = duration
        self.message = message
        self.color = color

    def __del__(self):
        """
        Explicitly clear the progress meter if the time-loop is destroyed.
        """
        self.clear()

    def __iter__(self) -> "TimeLoop":
        """
        Start the iterator.

        Creates and starts the progress meter
        """
        self.advent = self.last_moment = self.moment = pendulum.now()
        self.counter = 0
        self.progress = Progress()
        self.progress.add_task(
            f"[{self.color}]{self.message}...",
            total=self.duration.total_seconds(),
        )
        self.progress.start()
        return self

    def __next__(self) -> Tick:
        """
        Iterates the time loop and returns a tick.

        If the duration is complete, clear the progress meter and stop iteration.
        """
        progress: Progress = ArmasecCliError.enforce_defined(
            self.progress,
            "Progress bar has not been initialized...this should not happen",
        )

        self.counter += 1
        self.last_moment = self.moment
        self.moment: pendulum.DateTime = pendulum.now()
        elapsed: pendulum.Duration = self.moment - self.last_moment
        total_elapsed: pendulum.Duration = self.moment - self.advent

        for task_id in progress.task_ids:
            progress.advance(task_id, elapsed.total_seconds())

        if progress.finished:
            self.clear()
            raise StopIteration

        return Tick(
            counter=self.counter,
            elapsed=elapsed,
            total_elapsed=total_elapsed,
        )

    def clear(self):
        """
        Clear the time-loop.

        Stops the progress meter (if set) and reset moments, counter, progress meter.
        """
        if self.progress is not None:
            self.progress.stop()
        self.counter = 0
        self.progress = None
        self.moment = None
        self.last_moment = None
