from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", 30, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Breakfast", 10, "high"))

    assert len(pet.tasks) == 1


def test_completing_daily_task_adds_copy_due_tomorrow():
    pet = Pet("Luna", "cat")
    pet.add_task(Task("Thyroid meds", 5, "high", frequency="daily"))

    next_task = pet.mark_task_complete("Thyroid meds")

    assert pet.tasks[0].completed is True
    assert next_task is pet.tasks[1]
    assert next_task.completed is False
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task.pet_name == "Luna"


def test_completing_weekly_task_adds_copy_due_next_week():
    pet = Pet("Luna", "cat")
    pet.add_task(Task("Brushing", 15, "low", frequency="weekly"))

    next_task = pet.mark_task_complete("Brushing")

    assert next_task.due_date == date.today() + timedelta(weeks=1)


def test_completing_one_time_task_adds_nothing():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Vet visit", 60, "high", frequency="once"))

    assert pet.mark_task_complete("Vet visit") is None
    assert len(pet.tasks) == 1


def test_tomorrows_copy_is_not_in_todays_plan():
    owner = Owner("Jordan", 60)
    pet = Pet("Luna", "cat")
    owner.add_pet(pet)
    pet.add_task(Task("Thyroid meds", 5, "high", frequency="daily"))
    pet.mark_task_complete("Thyroid meds")

    assert Scheduler(owner).build_plan() == []
    tomorrow = Scheduler(owner, plan_date=date.today() + timedelta(days=1)).build_plan()
    assert [task.title for task in tomorrow] == ["Thyroid meds"]


def _owner_with(*pet_tasks):
    """Build an owner whose pets have the given (pet_name, Task) pairs."""
    owner = Owner("Jordan", 120)
    for pet_name, task in pet_tasks:
        pet = next((p for p in owner.pets if p.name == pet_name), None)
        if pet is None:
            pet = Pet(pet_name, "dog")
            owner.add_pet(pet)
        pet.add_task(task)
    return owner


def test_same_time_tasks_for_different_pets_conflict():
    owner = _owner_with(
        ("Mochi", Task("Breakfast", 10, "high", time="08:15")),
        ("Luna", Task("Breakfast", 5, "high", time="08:15")),
    )

    conflicts = Scheduler(owner).detect_conflicts()

    assert len(conflicts) == 1
    assert "different pets" in conflicts[0]


def test_overlapping_tasks_for_same_pet_conflict():
    owner = _owner_with(
        ("Mochi", Task("Morning walk", 30, "high", time="07:30")),
        ("Mochi", Task("Breakfast", 10, "high", time="07:45")),
    )

    conflicts = Scheduler(owner).detect_conflicts()

    assert len(conflicts) == 1
    assert "both for Mochi" in conflicts[0]


def test_back_to_back_and_untimed_tasks_do_not_conflict():
    owner = _owner_with(
        ("Mochi", Task("Morning walk", 30, "high", time="07:30")),
        ("Mochi", Task("Breakfast", 10, "high", time="08:00")),  # starts right as the walk ends
        ("Luna", Task("Brushing", 15, "low")),  # no set time
    )

    assert Scheduler(owner).detect_conflicts() == []


def test_completed_tasks_do_not_conflict():
    owner = _owner_with(
        ("Mochi", Task("Breakfast", 10, "high", time="08:15")),
        ("Luna", Task("Breakfast", 5, "high", time="08:15", completed=True)),
    )

    assert Scheduler(owner).detect_conflicts() == []


# --- Sorting -----------------------------------------------------------------


def test_sort_by_time_returns_chronological_order():
    owner = _owner_with(
        ("Mochi", Task("Fetch", 20, time="17:00")),
        ("Mochi", Task("Walk", 30, time="7:30")),  # no leading zero
        ("Luna", Task("Brushing", 15)),  # no set time
        ("Luna", Task("Meds", 5, time="08:00")),
    )

    ordered = Scheduler(owner).sort_by_time(owner.get_all_tasks())

    assert [task.title for task in ordered] == ["Walk", "Meds", "Fetch", "Brushing"]


def test_time_is_stored_zero_padded():
    assert Task("Walk", 30, time="7:30").time == "07:30"


# --- Building the daily plan -------------------------------------------------


def test_build_plan_orders_by_priority_with_back_to_back_times():
    owner = _owner_with(
        ("Mochi", Task("Fetch", 20, "low")),
        ("Mochi", Task("Walk", 30, "high")),
        ("Luna", Task("Brushing", 15, "medium")),
    )

    plan = Scheduler(owner, start_time="08:00").build_plan()

    assert [task.title for task in plan] == ["Walk", "Brushing", "Fetch"]
    assert [task.scheduled_time for task in plan] == ["08:00", "08:30", "08:45"]


def test_build_plan_skips_task_that_does_not_fit_but_fills_the_gap():
    owner = _owner_with(
        ("Mochi", Task("Walk", 30, "high")),
        ("Mochi", Task("Long hike", 60, "medium")),
        ("Luna", Task("Brushing", 15, "low")),
    )
    owner.available_minutes = 50

    scheduler = Scheduler(owner)
    plan = scheduler.build_plan()

    # The hike doesn't fit in the 20 minutes left after the walk, but brushing does.
    assert [task.title for task in plan] == ["Walk", "Brushing"]
    assert [task.title for task in scheduler.skipped] == ["Long hike"]


def test_build_plan_includes_task_that_exactly_fills_the_time():
    owner = _owner_with(("Mochi", Task("Walk", 30, "high")))
    owner.available_minutes = 30

    assert [task.title for task in Scheduler(owner).build_plan()] == ["Walk"]


def test_build_plan_with_no_time_skips_everything():
    owner = _owner_with(("Mochi", Task("Walk", 30, "high")))
    owner.available_minutes = 0

    scheduler = Scheduler(owner)

    assert scheduler.build_plan() == []
    assert [task.title for task in scheduler.skipped] == ["Walk"]


def test_build_plan_twice_does_not_duplicate_tasks():
    owner = _owner_with(("Mochi", Task("Walk", 30, "high")))
    scheduler = Scheduler(owner)

    scheduler.build_plan()
    scheduler.build_plan()

    assert len(scheduler.planned) == 1


def test_overdue_task_is_still_planned_today():
    yesterday = date.today() - timedelta(days=1)
    owner = _owner_with(("Mochi", Task("Walk", 30, "high", due_date=yesterday)))

    assert [task.title for task in Scheduler(owner).build_plan()] == ["Walk"]


def test_empty_owner_and_pet_without_tasks():
    owner = Owner("Jordan", 60)
    empty = Scheduler(owner)
    assert empty.build_plan() == []
    assert empty.detect_conflicts() == []
    assert "No pending tasks" in empty.explain_plan()

    owner.add_pet(Pet("Mochi", "dog"))
    assert Scheduler(owner).build_plan() == []


# --- Filtering ---------------------------------------------------------------


def test_filter_tasks_by_pet_status_and_both():
    owner = _owner_with(
        ("Mochi", Task("Walk", 30)),
        ("Mochi", Task("Breakfast", 10, completed=True)),
        ("Luna", Task("Brushing", 15)),
    )

    assert [t.title for t in owner.filter_tasks(pet_name="Mochi")] == ["Walk", "Breakfast"]
    assert [t.title for t in owner.filter_tasks(completed=False)] == ["Walk", "Brushing"]
    assert [t.title for t in owner.filter_tasks(pet_name="Mochi", completed=True)] == ["Breakfast"]
    assert len(owner.filter_tasks()) == 3


def test_filter_tasks_for_unknown_pet_returns_empty_list():
    owner = _owner_with(("Mochi", Task("Walk", 30)))

    assert owner.filter_tasks(pet_name="Rex") == []


# --- Recurring tasks ---------------------------------------------------------


def test_completing_overdue_daily_task_schedules_next_copy_from_today():
    pet = Pet("Luna", "cat")
    pet.add_task(Task("Meds", 5, frequency="daily", due_date=date.today() - timedelta(days=3)))

    next_task = pet.mark_task_complete("Meds")

    # Not 2 days ago (old due date + 1), which would already be overdue.
    assert next_task.due_date == date.today() + timedelta(days=1)


def test_completing_same_task_twice_does_not_complete_tomorrows_copy():
    pet = Pet("Luna", "cat")
    pet.add_task(Task("Meds", 5, frequency="daily"))
    pet.mark_task_complete("Meds")

    with pytest.raises(ValueError):
        pet.mark_task_complete("Meds")

    assert pet.tasks[1].completed is False  # tomorrow's copy is untouched


def test_completing_unknown_task_raises():
    pet = Pet("Luna", "cat")

    with pytest.raises(ValueError):
        pet.mark_task_complete("Nonexistent")


# --- Conflict detection ------------------------------------------------------


def test_duplicate_times_for_same_pet_are_flagged():
    owner = _owner_with(
        ("Mochi", Task("Walk", 30, time="08:00")),
        ("Mochi", Task("Breakfast", 10, time="08:00")),
    )

    conflicts = Scheduler(owner).detect_conflicts()

    assert len(conflicts) == 1
    assert "Walk" in conflicts[0] and "Breakfast" in conflicts[0]


def test_long_task_overlapping_two_later_tasks_gives_two_warnings():
    owner = _owner_with(
        ("Mochi", Task("Long walk", 60, time="08:00")),
        ("Luna", Task("Breakfast", 5, time="08:10")),
        ("Luna", Task("Meds", 5, time="08:30")),
    )

    # Breakfast and Meds don't overlap each other, but both overlap the walk.
    assert len(Scheduler(owner).detect_conflicts()) == 2


def test_task_due_tomorrow_does_not_conflict_with_today():
    tomorrow = date.today() + timedelta(days=1)
    owner = _owner_with(
        ("Mochi", Task("Walk", 30, time="08:00")),
        ("Luna", Task("Meds", 5, time="08:00", due_date=tomorrow)),
    )

    assert Scheduler(owner).detect_conflicts() == []


# --- Input validation --------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"priority": "urgent"},
        {"duration_minutes": 0},
        {"time": "8am"},
        {"time": "25:00"},
        {"frequency": "monthly"},
    ],
)
def test_invalid_task_input_raises(kwargs):
    fields = {"title": "Walk", "duration_minutes": 30, **kwargs}

    with pytest.raises(ValueError):
        Task(**fields)


def test_priority_is_case_insensitive():
    assert Task("Walk", 30, priority="High").priority == "high"
