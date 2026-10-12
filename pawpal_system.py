"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from itertools import combinations

# Single source of truth for valid priorities and their sort order (higher = more important).
PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}

# How far ahead the next copy of a recurring task is due; None means the task doesn't repeat.
FREQUENCY_INTERVAL = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1), "once": None}


def _check_priority(priority: str) -> str:
    """Normalize a priority string and make sure it's one we know how to rank."""
    priority = priority.strip().lower()
    if priority not in PRIORITY_RANK:
        raise ValueError(f"priority must be one of {list(PRIORITY_RANK)}, got {priority!r}")
    return priority


def _check_frequency(frequency: str) -> str:
    """Normalize a frequency string and make sure it's one we know how to repeat."""
    frequency = frequency.strip().lower()
    if frequency not in FREQUENCY_INTERVAL:
        raise ValueError(f"frequency must be one of {list(FREQUENCY_INTERVAL)}, got {frequency!r}")
    return frequency


def _check_duration(duration_minutes: int) -> int:
    """Make sure a duration is a positive number of minutes."""
    if duration_minutes <= 0:
        raise ValueError(f"duration_minutes must be positive, got {duration_minutes}")
    return duration_minutes


def _to_minutes(hhmm: str) -> int:
    """Convert "HH:MM" to minutes after midnight."""
    try:
        hours, minutes = (int(part) for part in hhmm.split(":"))
    except ValueError:
        raise ValueError(f"time must be HH:MM, got {hhmm!r}") from None
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        raise ValueError(f"time must be HH:MM, got {hhmm!r}")
    return hours * 60 + minutes


def _to_hhmm(minutes: int) -> str:
    """Convert minutes after midnight to "HH:MM"."""
    hours, minutes = divmod(minutes, 60)
    return f"{hours % 24:02d}:{minutes:02d}"


@dataclass
class Task:
    """A single pet care activity, such as a walk, feeding, or medication."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    category: str = "general"  # e.g. "walk", "feeding", "meds", "grooming", "enrichment"
    frequency: str = "daily"  # "daily", "weekly", or "once"
    completed: bool = False
    time: str | None = None  # preferred time of day, "HH:MM"; None means any time works
    due_date: date = field(default_factory=date.today)
    pet_name: str = ""  # set by Pet.add_task so the plan can say which pet a task is for
    scheduled_time: str | None = None  # "HH:MM", filled in by Scheduler.build_plan

    def __post_init__(self) -> None:
        """Validate and normalize priority and duration when a task is created."""
        self.priority = _check_priority(self.priority)
        self.duration_minutes = _check_duration(self.duration_minutes)
        self.frequency = _check_frequency(self.frequency)
        if self.time is not None:
            # Store as zero-padded "HH:MM" so times sort correctly as plain strings.
            self.time = _to_hhmm(_to_minutes(self.time))

    def update(self, duration_minutes: int | None = None, priority: str | None = None) -> None:
        """Change the task's duration and/or priority."""
        if duration_minutes is not None:
            self.duration_minutes = _check_duration(duration_minutes)
        if priority is not None:
            self.priority = _check_priority(priority)

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def next_occurrence(self) -> Task | None:
        """Return a fresh copy of this task for its next due date, or None if it doesn't repeat."""
        interval = FREQUENCY_INTERVAL[self.frequency]
        if interval is None:
            return None
        # Count from today if the task was done late, so the next copy isn't already overdue.
        next_due = max(self.due_date, date.today()) + interval
        return replace(self, due_date=next_due, completed=False, scheduled_time=None)

    def priority_rank(self) -> int:
        """Return a number for sorting, where higher means more important."""
        return PRIORITY_RANK[self.priority]


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet and tag it with this pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove the task with the given title."""
        for task in self.tasks:
            if task.title == title:
                self.tasks.remove(task)
                return
        raise ValueError(f"{self.name} has no task called {title!r}")

    def complete_task(self, task: Task) -> Task | None:
        """Mark this pet's task complete; if it repeats, add and return its next copy."""
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            self.add_task(next_task)
        return next_task

    def mark_task_complete(self, title: str) -> Task | None:
        """Complete the first pending task with this title that's due today or earlier (see complete_task).

        Future copies of recurring tasks are skipped, so calling this twice by mistake
        raises instead of quietly completing tomorrow's task early.
        """
        for task in self.tasks:
            if task.title == title and not task.completed and task.due_date <= date.today():
                return self.complete_task(task)
        raise ValueError(f"{self.name} has no task called {title!r} due today")

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are not completed yet."""
        return [task for task in self.tasks if not task.completed]


@dataclass
class Owner:
    """A pet owner, their daily time budget, and their pets."""

    name: str
    available_minutes: int
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove the pet with the given name."""
        for pet in self.pets:
            if pet.name == name:
                self.pets.remove(pet)
                return
        raise ValueError(f"{self.name} has no pet called {name!r}")

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return tasks matching the given pet name and/or completion status (None = don't filter)."""
        return [
            task
            for task in self.get_all_tasks()
            if (pet_name is None or task.pet_name == pet_name)
            and (completed is None or task.completed == completed)
        ]


class Scheduler:
    """Builds and explains a daily care plan for an owner's pets."""

    def __init__(self, owner: Owner, start_time: str = "08:00", plan_date: date | None = None) -> None:
        """Set up a scheduler for this owner, starting plan_date (default today) at start_time ("HH:MM")."""
        _to_minutes(start_time)  # fail early on a bad start time
        self.owner = owner
        self.start_time = start_time
        self.plan_date = plan_date or date.today()
        self.planned: list[Task] = []
        self.skipped: list[Task] = []

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered from most to least important.

        Ties are broken by shorter duration first, so more tasks fit in the day.
        """
        return sorted(tasks, key=lambda task: (-task.priority_rank(), task.duration_minutes))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by preferred time, earliest first; tasks with no time go last."""
        # Zero-padded "HH:MM" strings compare correctly as text ("07:30" < "18:00"),
        # and False sorts before True, so timed tasks come before untimed ones.
        return sorted(tasks, key=lambda task: (task.time is None, task.time or ""))

    def due_tasks(self) -> list[Task]:
        """Return pending tasks due on the plan date, plus any overdue ones.

        Future copies of recurring tasks wait for their own day.
        """
        return [
            task
            for task in self.owner.get_all_tasks()
            if not task.completed and task.due_date <= self.plan_date
        ]

    def detect_conflicts(self) -> list[str]:
        """Return a warning for each pair of due tasks whose preferred time slots overlap.

        Works across pets too, since the owner can't do two things at once. Returns an
        empty list when there are no conflicts; it never raises.
        """
        timed = self.sort_by_time([task for task in self.due_tasks() if task.time is not None])
        warnings = []
        # Check every pair once. Because the list is sorted, `first` never starts after
        # `second`, so they overlap exactly when `second` starts before `first` ends.
        # Checking all pairs (O(n^2)) also catches one long task overlapping several later
        # ones, and is plenty fast for a day of pet care.
        for first, second in combinations(timed, 2):
            first_end = _to_minutes(first.time) + first.duration_minutes
            if _to_minutes(second.time) < first_end:
                who = f"both for {first.pet_name}" if first.pet_name == second.pet_name else "different pets"
                second_end = _to_minutes(second.time) + second.duration_minutes
                warnings.append(
                    f"Conflict ({who}): {first.title} for {first.pet_name} "
                    f"({first.time}-{_to_hhmm(first_end)}) overlaps {second.title} for "
                    f"{second.pet_name} ({second.time}-{_to_hhmm(second_end)})"
                )
        return warnings

    def build_plan(self) -> list[Task]:
        """Choose and order tasks that fit in the owner's available time.

        Resets planned/skipped first so calling it again doesn't duplicate tasks,
        and sets each planned task's scheduled_time starting from start_time.
        """
        self.planned = []
        self.skipped = []

        pending = self.due_tasks()
        time_left = self.owner.available_minutes
        clock = _to_minutes(self.start_time)

        for task in self.sort_tasks(pending):
            task.scheduled_time = None
            if task.duration_minutes <= time_left:
                task.scheduled_time = _to_hhmm(clock)
                clock += task.duration_minutes
                time_left -= task.duration_minutes
                self.planned.append(task)
            else:
                self.skipped.append(task)

        return self.planned

    def explain_plan(self) -> str:
        """Describe why each task was planned or skipped."""
        if not self.planned and not self.skipped:
            return f"No pending tasks to schedule for {self.owner.name}."

        used = sum(task.duration_minutes for task in self.planned)
        lines = [
            f"Plan for {self.owner.name}: {used} of {self.owner.available_minutes} "
            f"available minutes used, starting at {self.start_time}.",
            "Tasks are ordered by priority (high first), then shortest first.",
        ]

        for task in self.planned:
            lines.append(
                f"  {task.scheduled_time} - {task.title} for {task.pet_name} "
                f"({task.duration_minutes} min, {task.priority} priority)"
            )

        if self.skipped:
            lines.append("Skipped (not enough time left):")
            for task in self.skipped:
                lines.append(
                    f"  {task.title} for {task.pet_name} "
                    f"({task.duration_minutes} min, {task.priority} priority)"
                )

        return "\n".join(lines)
