# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

1. **Enter owner and pet info.** The user gives basic details about themselves and their pet, such as the owner's name, how much time they have for pet care today, and the pet's name and species. The app uses this to personalize the plan and to know how much time it can fill.
2. **Add and manage care tasks.** The user adds care tasks like walks, feeding, medication, grooming or enrichment. Each task has at least a duration and a priority. The user can also edit or remove tasks as their pet's needs change.
3. **Generate and view today's plan.** The user asks the app to build a daily schedule. The app picks and orders tasks based on priority and the time available, shows the plan clearly, and explains why it chose it. For example, it might say a high-priority medication was scheduled first, or that a low-priority task was skipped because time ran out.

**a. Initial design**

My initial UML (`diagrams/uml.mmd`) has four classes. An Owner has one or more Pets, each Pet has a list of Tasks, and a Scheduler reads the owner's pets and tasks to build the day's plan.

- **Owner** holds the owner's name, how many minutes they have for pet care today, their preferences, and their pets. It can add or remove a pet and collect every task across all pets.
- **Pet** holds the pet's name, species, age, and care tasks. It can add or remove a task and return the tasks that aren't done yet.
- **Task** holds one care activity: its title, duration in minutes, priority (low/medium/high), category (walk, feeding, meds, etc.), frequency (daily/weekly), and whether it's completed. It can be updated, marked complete, and turn its priority into a number for sorting.
- **Scheduler** takes an Owner and a start time. It sorts tasks by priority, fits as many as possible into the owner's available time, keeps lists of planned and skipped tasks, and explains why it made each choice.

**b. Design changes**

Yes. After writing the class skeleton, I asked my AI assistant to review `pawpal_system.py` for missing relationships and logic bottlenecks. I made three changes:

- **Tasks now remember which pet they belong to (`Task.pet_name`).** `Owner.get_all_tasks()` combines every pet's tasks into one list, so once the Scheduler gets that list it can't tell whose task is whose. With two pets that both have a "Feeding" task, the plan would be confusing. `Pet.add_task` now tags each task with the pet's name, so the plan can say "Feeding (Mochi)."
- **Tasks get a scheduled time (`Task.scheduled_time`).** The app is supposed to explain *when* each task happens, but the original design only had a start time on the Scheduler and nowhere to store each task's time slot. `build_plan` will now fill in an "HH:MM" time for every planned task.
- **Priorities come from one shared table (`PRIORITY_RANK`).** Priority is a plain string, so a typo like "High" or "urgent" would quietly break sorting. A single `{"low": 1, "medium": 2, "high": 3}` mapping is now the one place that defines which priorities are valid and how they rank.

I also noted that `build_plan` has to clear `planned` and `skipped` before it runs. Otherwise, clicking "Generate schedule" twice would duplicate tasks.

The review raised a few other points that I decided to leave for later phases. `Owner.preferences` isn't used by the Scheduler yet. `frequency` doesn't do anything until the scheduler knows what day it is. And removing tasks or pets by name is ambiguous if two of them share a name.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

**Conflicts are warnings, not fixes.** When two tasks have overlapping set times, `Scheduler.detect_conflicts()` only returns a warning message such as "Breakfast for Mochi (08:15-08:25) overlaps Flea treatment for Mochi (08:20-08:25)." It doesn't move either task or refuse to make a plan. The scheduler also checks for *overlapping* time slots rather than only identical start times, and it checks all pairs of tasks, across different pets too, since one owner can't do two things at once.

This is reasonable for a pet owner because the owner knows things the app doesn't. Two breakfasts at 08:15 might be fine if the bowls go down together. A walk overlapping meds is a real problem. Automatically moving a task could push medication to the wrong time, which is worse than a clear warning. Checking every pair is slower in theory, but a day of pet care has a handful of tasks, so it's instant in practice. A faster approach that only compares neighbouring tasks would miss a long walk that overlaps two later tasks.

A related tradeoff: `build_plan()` picks tasks greedily by priority (high first, shorter first among ties) and keeps anything that fits in the time left. That can leave a few minutes unused where a smarter "best fit" search might fill them exactly. But the greedy rule is easy to explain ("high priority comes first") and predictable, which matters more to a busy owner than squeezing in one extra low-priority task.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

When I asked the AI how to simplify `detect_conflicts()`, it offered three options. The first used `itertools.combinations` to loop over every pair of tasks. The second was a faster "sweep" that tracks only the latest end time. The third packed the whole check into one nested list comprehension. I kept the `combinations` version because it removed the index juggling (`enumerate` plus `timed[:i]`) and reads like the idea itself: "check every pair." I rejected the sweep because it only remembers one earlier task, so it can miss a pair when three tasks overlap. It's faster, but for a few pet tasks correctness matters more than speed. I rejected the one-line comprehension because it was the most "Pythonic" but much harder to read. I checked the change by re-running the test suite (all 10 tests passed) and confirming `main.py` printed the same two conflict warnings as before.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
