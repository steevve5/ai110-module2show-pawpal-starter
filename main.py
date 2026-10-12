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


def print_tasks(heading: str, tasks: list[Task]) -> None:
    """Print a short titled list of tasks with their time, pet, and status."""
    print()
    print(f"  {heading}")
    if not tasks:
        print("    (none)")
    for task in tasks:
        status = "done" if task.completed else "to do"
        print(
            f"    {task.time or '--:--'}  {task.title:<16}{task.pet_name:<7}"
            f"{task.frequency:<8}due {task.due_date:%a %b %d}  {status}"
        )


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added out of time order on purpose, to show sort_by_time putting them back in order.
    mochi.add_task(Task("Fetch in yard", 20, "medium", "enrichment", time="17:00"))
    mochi.add_task(Task("Morning walk", 30, "high", "walk", time="7:30"))
    luna.add_task(Task("Laser play", 25, "low", "enrichment", time="19:00"))
    luna.add_task(Task("Thyroid meds", 5, "high", "meds", time="08:00"))
    mochi.add_task(Task("Breakfast", 10, "high", "feeding", time="08:15"))
    luna.add_task(Task("Brushing", 15, "low", "grooming", frequency="weekly"))  # no preferred time
    luna.add_task(Task("Breakfast", 5, "high", "feeding", time="08:15"))  # same time as Mochi's breakfast
    mochi.add_task(Task("Flea treatment", 5, "medium", "meds", time="08:20"))  # during Mochi's breakfast

    # Luna's daily meds are already done today; completing a recurring task queues tomorrow's copy.
    next_meds = luna.mark_task_complete("Thyroid meds")
    print()
    print(f"  Completed Luna's Thyroid meds -> next one added for {next_meds.due_date:%a %b %d}")

    scheduler = Scheduler(owner, start_time="07:30")

    print_tasks("All tasks, in the order they were added:", owner.get_all_tasks())
    print_tasks("Sorted by time (sort_by_time):", scheduler.sort_by_time(owner.get_all_tasks()))
    print_tasks("Only Luna's tasks (filter_tasks pet_name='Luna'):", owner.filter_tasks(pet_name="Luna"))
    print_tasks("Still to do (filter_tasks completed=False):", owner.filter_tasks(completed=False))
    print_tasks(
        "Mochi's tasks still to do, sorted by time:",
        scheduler.sort_by_time(owner.filter_tasks(pet_name="Mochi", completed=False)),
    )
    print()

    print("  Conflict check (detect_conflicts):")
    conflicts = scheduler.detect_conflicts()
    for warning in conflicts:
        print(f"    WARNING: {warning}")
    if not conflicts:
        print("    No conflicts.")
    print()

    scheduler.build_plan()
    print_schedule(scheduler)


if __name__ == "__main__":
    main()
