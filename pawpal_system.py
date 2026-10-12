"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet care activity, such as a walk, feeding, or medication."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    category: str = "general"  # e.g. "walk", "feeding", "meds", "grooming", "enrichment"
    frequency: str = "daily"  # "daily" or "weekly"
    completed: bool = False

    def update(self, duration_minutes: int | None = None, priority: str | None = None) -> None:
        """Change the task's duration and/or priority."""
        pass

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def priority_rank(self) -> int:
        """Return a number for sorting, where higher means more important."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove the task with the given title."""
        pass

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are not completed yet."""
        pass


@dataclass
class Owner:
    """A pet owner, their daily time budget, and their pets."""

    name: str
    available_minutes: int
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, name: str) -> None:
        """Remove the pet with the given name."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        pass


class Scheduler:
    """Builds and explains a daily care plan for an owner's pets."""

    def __init__(self, owner: Owner, start_time: str = "08:00") -> None:
        self.owner = owner
        self.start_time = start_time
        self.planned: list[Task] = []
        self.skipped: list[Task] = []

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered from most to least important."""
        pass

    def build_plan(self) -> list[Task]:
        """Choose and order tasks that fit in the owner's available time."""
        pass

    def explain_plan(self) -> str:
        """Describe why each task was planned or skipped."""
        pass
