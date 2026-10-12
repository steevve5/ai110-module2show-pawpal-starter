# 🐾 PawPal+

PawPal+ is a Streamlit app that helps a busy pet owner stay consistent with pet care. You enter your pets and their care tasks (walks, feeding, meds, grooming, play), say how much time you have today, and PawPal+ builds a daily plan that puts the most important tasks first. It explains what it planned and what didn't fit, warns you when two tasks clash, and brings recurring tasks back automatically.

## ✨ Features

- **Owner and multi-pet profiles:** one owner with a daily time budget and any number of pets.
- **Care tasks with real details:** each task has a duration, a priority (low/medium/high), a category, an optional set time, and how often it repeats. Bad input (a 0-minute task, a priority like "urgent", a time like "25:00") is rejected with a clear message.
- **Priority-based daily plan:** `Scheduler.build_plan()` plans high-priority tasks first (shortest first among ties), keeps every task that fits in your available minutes, gives each one a start time, and lists what was skipped.
- **Plan explanations:** `Scheduler.explain_plan()` says how many minutes were used, how tasks were ordered, and why anything was left out.
- **Sorting by time:** `Scheduler.sort_by_time()` puts tasks in time-of-day order using "HH:MM" string sorting, with untimed tasks last.
- **Filtering by pet and status:** `Owner.filter_tasks()` shows one pet's tasks, only what's left to do, only what's done, or any combination.
- **Daily and weekly recurrence:** completing a `daily` or `weekly` task automatically adds the next copy, due tomorrow or in a week (`timedelta`). `once` tasks don't repeat. Future copies stay out of today's plan, and completing the same task twice by mistake won't complete tomorrow's copy.
- **Conflict warnings:** `Scheduler.detect_conflicts()` flags any two tasks whose time slots overlap, for the same pet or different pets, and shows a warning instead of crashing. Back-to-back tasks don't count as conflicts.
- **Tested:** 33 automated tests cover sorting, planning, filtering, recurrence, conflicts, and input validation.

## 🚀 Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run it

```bash
streamlit run app.py      # the web app
python main.py            # terminal demo of every scheduling feature
python -m pytest          # the test suite
```

> If you edit `pawpal_system.py` while the app is running, restart `streamlit run`. Streamlit reloads `app.py` on save but not the modules it imports.

### Project structure

| File | What it is |
|------|------------|
| `pawpal_system.py` | Logic layer: the `Task`, `Pet`, `Owner`, and `Scheduler` classes |
| `app.py` | Streamlit UI that calls the logic layer |
| `main.py` | Terminal demo script |
| `tests/test_pawpal.py` | Automated tests (pytest) |
| `diagrams/uml_final.mmd` | Final Mermaid class diagram (paste into [mermaid.live](https://mermaid.live/) to view) |
| `reflection.md` | Design decisions, tradeoffs, and reflection |

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

Run the full test suite from the project folder:

```bash
python -m pytest
```

Add `-v` to see each test by name. All tests live in `tests/test_pawpal.py` and cover the logic layer in `pawpal_system.py`:

| Area | What the tests check |
|------|----------------------|
| **Basics** | `mark_complete()` changes a task's status; `add_task()` increases a pet's task count. |
| **Sorting** | `sort_by_time()` returns tasks in chronological order with untimed tasks last; "7:30" is stored as "07:30" so it sorts correctly. |
| **Daily plan** | High priority goes first with back-to-back times; a task that doesn't fit is skipped while a shorter one fills the gap; a task that exactly fills the remaining time is kept; 0 minutes skips everything; re-running doesn't duplicate tasks; overdue tasks are still planned; an owner with no pets or a pet with no tasks gives an empty plan. |
| **Filtering** | `filter_tasks()` by pet, by status, and both; an unknown pet name returns an empty list. |
| **Recurring tasks** | Completing a daily task adds a copy due tomorrow, weekly adds one due in 7 days, and `once` adds nothing; tomorrow's copy is left out of today's plan; a late completion schedules the next copy from today; completing the same task twice doesn't complete tomorrow's copy early. |
| **Conflict detection** | Same time for two pets and duplicate times for one pet are flagged; partial overlaps are flagged; one long task overlapping two later tasks gives two warnings; back-to-back, untimed, completed, and not-yet-due tasks are not flagged. |
| **Input validation** | Invalid priority, a duration of 0, bad times ("8am", "25:00"), and unknown frequencies raise `ValueError`; priority is case-insensitive. |

Sample test output:

```
============================= test session starts =============================
platform win32 -- Python 3.12.4, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\gstev\ai110-module2show-pawpal-starter
plugins: anyio-4.9.0
collected 33 items

tests\test_pawpal.py .................................                   [100%]

============================= 33 passed in 0.06s ==============================
```

**Confidence level: ⭐⭐⭐⭐☆ (4/5)**

The scheduling logic is well covered. All 33 tests pass, including edge cases like exact-fit time budgets, overlapping conflicts, and late or repeated completions of recurring tasks. I also checked that the tests can fail: temporarily restoring an older bug made exactly the matching test fail. I'm holding back the fifth star because:

- The Streamlit UI (`app.py`) is only checked by hand in the browser, not by automated tests.
- Plans that run past midnight wrap around to "00:00" and aren't handled or tested.
- `build_plan()` doesn't yet place tasks at their own set times (see Known limitations below).

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
- Plans that run past midnight wrap around to "00:00".
- Data lives in the browser session only: refreshing the page or restarting the app starts fresh.

## 📸 Demo Walkthrough

### What you can do in the app

| Section | Actions |
|---------|---------|
| **Owner** | Set your name and how many minutes you have for pet care today. |
| **Pets** | Add a pet (name, species, age). Duplicate or blank names are rejected. The pets table shows how many tasks each pet has. |
| **Tasks** | Add a task for a pet: title, category, duration, priority, how often it repeats, and optionally a set time. Filter the task list by pet and status, sort it by time of day or priority, and mark a task complete. Time conflicts appear as a yellow warning right under the list. |
| **Build Schedule** | Pick a start time and click **Generate schedule** to see today's plan, what didn't fit, and a "Why this plan?" explanation. |

### Example workflow

1. **Set up the owner.** Enter "Jordan" as the owner and set **Minutes available today** to 60.
2. **Add pets.** In **Pets**, add "Mochi" (dog), then "Luna" (cat). Both appear in the pets table with 0 tasks.
3. **Add tasks.** In **Tasks**, choose Mochi and add "Morning walk" (30 min, high, daily). Tick **Must happen at a set time** and pick 08:00. Then add "Breakfast" for Luna (5 min, high, daily), also set at 08:00, and "Brushing" for Luna (15 min, low, weekly) with no set time. Each task shows up in the table, and the pets table's task count updates.
4. **See a conflict warning.** Because the walk (08:00-08:30) and Luna's breakfast (08:00-08:05) overlap, a yellow warning appears under the task list: *"⚠️ 1 time conflict today. Conflict (different pets): Morning walk for Mochi (08:00-08:30) overlaps Breakfast for Luna (08:00-08:05)"*, with a suggestion to change one time or ignore it if you can do both.
5. **Sort and filter.** Set **Sort by** to "Time of day" to see the 08:00 tasks first and Brushing ("any") last. Set **Show pet** to "Luna" to see only Luna's tasks.
6. **Generate the schedule.** Click **Generate schedule**. A green summary shows "3 tasks, 50 of 60 minutes planned", followed by the plan table in priority order: Luna's breakfast, Mochi's walk, then Brushing. Open **Why this plan?** for the full explanation.
7. **Complete a recurring task.** Under **Mark a task complete**, choose Luna's breakfast and click **Mark complete**. The app confirms *"Next 'Breakfast' for Luna is due"* tomorrow; today's copy shows ✅ done and a new copy due tomorrow appears in the list (set **Show** to "All" to see both).
8. **Re-plan.** Click **Generate schedule** again. Luna's breakfast is gone from today's plan, because it's done and tomorrow's copy isn't due yet.

### Scheduler behaviors on display

- **Priority planning:** high-priority tasks are planned first. If time runs out, lower-priority tasks are listed as skipped with a tip to add time.
- **Sorting by time:** the task list can be ordered by time of day, with untimed tasks last.
- **Filtering:** by pet and by status (to do, done, all).
- **Conflict warnings:** overlapping set times, across pets too, are flagged as soon as they exist.
- **Recurrence:** completing a daily or weekly task schedules the next one, and future copies stay off today's plan.

### Sample CLI output

`python main.py` runs the same logic in the terminal with two pets and nine tasks. It completes a recurring task, sorts and filters the task list, checks for conflicts, and prints today's schedule:

```
  Completed Luna's Thyroid meds -> next one added for Mon Oct 12

  All tasks, in the order they were added:
    17:00  Fetch in yard   Mochi  daily   due Sun Oct 11  to do
    07:30  Morning walk    Mochi  daily   due Sun Oct 11  to do
    08:15  Breakfast       Mochi  daily   due Sun Oct 11  to do
    08:20  Flea treatment  Mochi  daily   due Sun Oct 11  to do
    19:00  Laser play      Luna   daily   due Sun Oct 11  to do
    08:00  Thyroid meds    Luna   daily   due Sun Oct 11  done
    --:--  Brushing        Luna   weekly  due Sun Oct 11  to do
    08:15  Breakfast       Luna   daily   due Sun Oct 11  to do
    08:00  Thyroid meds    Luna   daily   due Mon Oct 12  to do

  Sorted by time (sort_by_time):
    07:30  Morning walk    Mochi  daily   due Sun Oct 11  to do
    08:00  Thyroid meds    Luna   daily   due Sun Oct 11  done
    08:00  Thyroid meds    Luna   daily   due Mon Oct 12  to do
    08:15  Breakfast       Mochi  daily   due Sun Oct 11  to do
    08:15  Breakfast       Luna   daily   due Sun Oct 11  to do
    08:20  Flea treatment  Mochi  daily   due Sun Oct 11  to do
    17:00  Fetch in yard   Mochi  daily   due Sun Oct 11  to do
    19:00  Laser play      Luna   daily   due Sun Oct 11  to do
    --:--  Brushing        Luna   weekly  due Sun Oct 11  to do

  Only Luna's tasks (filter_tasks pet_name='Luna'):
    19:00  Laser play      Luna   daily   due Sun Oct 11  to do
    08:00  Thyroid meds    Luna   daily   due Sun Oct 11  done
    --:--  Brushing        Luna   weekly  due Sun Oct 11  to do
    08:15  Breakfast       Luna   daily   due Sun Oct 11  to do
    08:00  Thyroid meds    Luna   daily   due Mon Oct 12  to do

  Still to do (filter_tasks completed=False):
    17:00  Fetch in yard   Mochi  daily   due Sun Oct 11  to do
    07:30  Morning walk    Mochi  daily   due Sun Oct 11  to do
    08:15  Breakfast       Mochi  daily   due Sun Oct 11  to do
    08:20  Flea treatment  Mochi  daily   due Sun Oct 11  to do
    19:00  Laser play      Luna   daily   due Sun Oct 11  to do
    --:--  Brushing        Luna   weekly  due Sun Oct 11  to do
    08:15  Breakfast       Luna   daily   due Sun Oct 11  to do
    08:00  Thyroid meds    Luna   daily   due Mon Oct 12  to do

  Mochi's tasks still to do, sorted by time:
    07:30  Morning walk    Mochi  daily   due Sun Oct 11  to do
    08:15  Breakfast       Mochi  daily   due Sun Oct 11  to do
    08:20  Flea treatment  Mochi  daily   due Sun Oct 11  to do
    17:00  Fetch in yard   Mochi  daily   due Sun Oct 11  to do

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
