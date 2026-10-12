# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Output from running `python main.py` (one owner with 90 minutes, a dog and a cat). This is the end of the output: the conflict check and the generated plan. The full run also prints the sorted and filtered task lists shown under Smarter Scheduling.

```
  Conflict check (detect_conflicts):
    WARNING: Conflict (different pets): Breakfast for Mochi (08:15-08:25) overlaps Breakfast for Luna (08:15-08:20)
    WARNING: Conflict (both for Mochi): Breakfast for Mochi (08:15-08:25) overlaps Flea treatment for Mochi (08:20-08:25)

========================================================
  Today's Schedule for Jordan
  85 of 90 minutes planned, starting 07:30
========================================================
  Time   Task              Pet       Length  Priority
  ----------------------------------------------------
  07:30  Breakfast         Luna       5 min  high
  07:35  Breakfast         Mochi     10 min  high
  07:45  Morning walk      Mochi     30 min  high
  08:15  Flea treatment    Mochi      5 min  medium
  08:20  Fetch in yard     Mochi     20 min  medium
  08:40  Brushing          Luna      15 min  low

  Skipped (not enough time left):
    - Laser play for Luna (25 min, low)
========================================================
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

All of this logic lives in `pawpal_system.py`, and `python main.py` demonstrates each feature.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_tasks()` | `sort_by_time` orders tasks by their set `time` ("HH:MM"), earliest first, with untimed tasks last. `sort_tasks` orders by priority (high first), then shortest first, and is what the daily plan uses. |
| Filtering | `Owner.filter_tasks(pet_name=None, completed=None)`, `Scheduler.due_tasks()` | Filter by pet, by done or not done, or both. A filter left as `None` isn't applied. `due_tasks` keeps only pending tasks due on the plan date (or overdue). |
| Conflict handling | `Scheduler.detect_conflicts()` | Flags any two due tasks whose time slots *overlap*, not just identical start times, for the same pet or different pets. Returns warning messages instead of raising. |
| Recurring tasks | `Task.next_occurrence()`, `Pet.complete_task()`, `Pet.mark_task_complete()` | Completing a `daily` or `weekly` task adds a fresh copy due 1 or 7 days later (using `timedelta`). `once` tasks don't repeat. Tomorrow's copy stays out of today's plan. |
| Fitting the day | `Scheduler.build_plan()`, `Scheduler.explain_plan()` | Goes through tasks by priority, keeps each one that fits in the owner's remaining minutes, assigns start times, and explains what was planned or skipped. |

### Sorting

Times are stored zero-padded ("7:30" becomes "07:30"), so they sort correctly as plain strings with a `lambda` key:

```python
sorted(tasks, key=lambda task: (task.time is None, task.time or ""))
```

`task.time is None` is `False` for timed tasks and `True` for untimed ones. Since `False` sorts before `True`, untimed tasks land at the end.

### Filtering

```python
owner.filter_tasks(pet_name="Luna")                    # all of Luna's tasks
owner.filter_tasks(completed=False)                    # everything still to do
owner.filter_tasks(pet_name="Mochi", completed=False)  # Mochi's remaining tasks
```

### Conflict detection

`detect_conflicts()` takes the due tasks that have a set time, sorts them by time, and checks every pair with `itertools.combinations`. Because the list is sorted, two tasks overlap exactly when the later one starts before the earlier one ends. Tasks that run back to back (a walk ending at 08:00 and breakfast at 08:00) are not conflicts. Completed tasks and tasks with no set time are ignored.

```
WARNING: Conflict (different pets): Breakfast for Mochi (08:15-08:25) overlaps Breakfast for Luna (08:15-08:20)
WARNING: Conflict (both for Mochi): Breakfast for Mochi (08:15-08:25) overlaps Flea treatment for Mochi (08:20-08:25)
```

Conflicts are warnings, not automatic fixes. The owner decides whether a clash matters (see `reflection.md`, section 2b).

### Recurring tasks

Each task has a `due_date` (default: today) and a `frequency` of `daily`, `weekly`, or `once`. Calling `pet.mark_task_complete("Thyroid meds")` marks today's task done and adds a new copy due `today + timedelta(days=1)`. If a task is completed late, the next copy is counted from today so it isn't already overdue. The Streamlit app's **Mark complete** button uses the same `Pet.complete_task()` method.

### Known limitations

- `build_plan()` assigns start times by packing tasks one after another from the start time. It doesn't yet place a task at its own set `time`; set times are used for sorting and conflict checks.
- The Streamlit form can't set a task's time yet, so conflict warnings currently show only in the terminal demo.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
