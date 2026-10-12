"""Temporary testing ground: build a sample owner and print today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(scheduler: Scheduler) -> None:
    """Print the planned and skipped tasks as a readable table."""
    owner = scheduler.owner
    used = sum(task.duration_minutes for task in scheduler.planned)

    print("=" * 56)
    print(f"  Today's Schedule for {owner.name}")
    print(f"  {used} of {owner.available_minutes} minutes planned, starting {scheduler.start_time}")
    print("=" * 56)
    print(f"  {'Time':<7}{'Task':<18}{'Pet':<8}{'Length':>8}  Priority")
    print("  " + "-" * 52)
    for task in scheduler.planned:
        print(
            f"  {task.scheduled_time:<7}{task.title:<18}{task.pet_name:<8}"
            f"{task.duration_minutes:>4} min  {task.priority}"
        )

    if scheduler.skipped:
        print()
        print("  Skipped (not enough time left):")
        for task in scheduler.skipped:
            print(f"    - {task.title} for {task.pet_name} ({task.duration_minutes} min, {task.priority})")
    print("=" * 56)


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", 30, "high", "walk"))
    mochi.add_task(Task("Breakfast", 10, "high", "feeding"))
    mochi.add_task(Task("Fetch in yard", 20, "medium", "enrichment"))
    luna.add_task(Task("Breakfast", 5, "high", "feeding"))
    luna.add_task(Task("Thyroid meds", 5, "high", "meds"))
    luna.add_task(Task("Brushing", 15, "low", "grooming"))
    luna.add_task(Task("Laser play", 25, "low", "enrichment"))

    scheduler = Scheduler(owner, start_time="07:30")
    scheduler.build_plan()
    print_schedule(scheduler)


if __name__ == "__main__":
    main()
