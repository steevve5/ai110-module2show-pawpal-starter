from datetime import date, timedelta

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
