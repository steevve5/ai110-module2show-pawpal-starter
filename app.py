import datetime

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' care for the day based on priority and the time you have.")

# Streamlit reruns this whole script on every click, so keep the Owner in session_state.
# Only create it the first time; after that, reuse the same object (and its pets/tasks).
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=60)

owner: Owner = st.session_state.owner

# --- Owner ---------------------------------------------------------------
st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = int(
        st.number_input(
            "Minutes available today", min_value=0, max_value=1440, value=owner.available_minutes, step=5
        )
    )

# --- Pets ----------------------------------------------------------------
st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age", min_value=0, max_value=40, value=0)
    if st.form_submit_button("Add pet"):
        pet_name = pet_name.strip()
        if not pet_name:
            st.error("Please enter a pet name.")
        elif any(pet.name == pet_name for pet in owner.pets):
            st.error(f"You already have a pet named {pet_name}.")
        else:
            owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))
            st.success(f"Added {pet_name}.")

if owner.pets:
    st.table(
        [{"Name": pet.name, "Species": pet.species, "Age": pet.age, "Tasks": len(pet.tasks)} for pet in owner.pets]
    )
else:
    st.info("No pets yet. Add one above.")

def show_conflicts(scheduler: Scheduler) -> None:
    """Show any time conflicts as one warning, with what overlaps and what to do about it."""
    conflicts = scheduler.detect_conflicts()
    if not conflicts:
        return
    plural = "s" if len(conflicts) > 1 else ""
    st.warning(
        f"**⚠️ {len(conflicts)} time conflict{plural} today.** You can't be in two places at once:\n\n"
        + "\n".join(f"- {conflict}" for conflict in conflicts)
        + "\n\nChange one task's time, or ignore this if you can do both together (like setting down two food bowls).",
    )


def task_rows(tasks: list[Task]) -> list[dict]:
    """Turn tasks into table rows for st.table."""
    return [
        {
            "Time": task.time or "any",
            "Pet": task.pet_name,
            "Task": task.title,
            "Minutes": task.duration_minutes,
            "Priority": task.priority,
            "Repeats": task.frequency,
            "Due": task.due_date.strftime("%a %b %d"),
            "Status": "✅ done" if task.completed else "to do",
        }
        for task in tasks
    ]


# --- Tasks ---------------------------------------------------------------
st.subheader("Tasks")
if not owner.pets:
    st.caption("Add a pet first, then you can give it care tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            pet_choice = st.selectbox("For pet", [pet.name for pet in owner.pets])
            task_title = st.text_input("Task title", placeholder="Morning walk")
            category = st.selectbox("Category", ["walk", "feeding", "meds", "grooming", "enrichment", "general"])
            has_time = st.checkbox("Must happen at a set time")
            task_time = st.time_input("Set time", value=datetime.time(8, 0), step=datetime.timedelta(minutes=15))
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            frequency = st.selectbox("Repeats", ["daily", "weekly", "once"])
        if st.form_submit_button("Add task"):
            if not task_title.strip():
                st.error("Please enter a task title.")
            else:
                pet = next(pet for pet in owner.pets if pet.name == pet_choice)
                pet.add_task(
                    Task(
                        title=task_title.strip(),
                        duration_minutes=int(duration),
                        priority=priority,
                        category=category,
                        frequency=frequency,
                        time=task_time.strftime("%H:%M") if has_time else None,
                    )
                )
                st.session_state.flash = f"Added '{task_title.strip()}' for {pet.name}."
                st.rerun()  # rerun so the pets table above shows the new task count

    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))

    if owner.get_all_tasks():
        # Filter and sort with the logic layer: Owner.filter_tasks + Scheduler.sort_by_time / sort_tasks.
        col1, col2, col3 = st.columns(3)
        with col1:
            pet_filter = st.selectbox("Show pet", ["All pets"] + [pet.name for pet in owner.pets])
        with col2:
            status_filter = st.selectbox("Show", ["To do", "Done", "All"])
        with col3:
            sort_choice = st.selectbox("Sort by", ["Time of day", "Priority"])

        tasks = owner.filter_tasks(
            pet_name=None if pet_filter == "All pets" else pet_filter,
            completed={"To do": False, "Done": True, "All": None}[status_filter],
        )
        sorter = Scheduler(owner)
        tasks = sorter.sort_by_time(tasks) if sort_choice == "Time of day" else sorter.sort_tasks(tasks)

        if tasks:
            st.table(task_rows(tasks))
        else:
            st.info("No tasks match these filters.")

        show_conflicts(Scheduler(owner))
    else:
        st.info("No tasks yet. Add one above.")

    pending = owner.filter_tasks(completed=False)
    if pending:
        with st.form("complete_task"):
            labels = [f"{task.pet_name}: {task.title} (due {task.due_date:%a %b %d})" for task in pending]
            choice = st.selectbox("Mark a task complete", range(len(pending)), format_func=lambda i: labels[i])
            if st.form_submit_button("Mark complete"):
                task = pending[choice]
                pet = next(pet for pet in owner.pets if pet.name == task.pet_name)
                next_task = pet.complete_task(task)  # recurring tasks get their next copy added
                if next_task is not None:
                    st.session_state.flash = (
                        f"Done! Next '{task.title}' for {pet.name} is due {next_task.due_date:%a %b %d}."
                    )
                else:
                    st.session_state.flash = f"Done! '{task.title}' for {pet.name} won't repeat."
                st.rerun()  # rerun so the task table above shows the change

st.divider()

# --- Schedule ------------------------------------------------------------
st.subheader("Build Schedule")
start = st.time_input("Start time", value=datetime.time(8, 0), step=datetime.timedelta(minutes=15))

if st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner, start_time=start.strftime("%H:%M"))
    scheduler.build_plan()

    if not scheduler.planned and not scheduler.skipped:
        st.info("There are no tasks due today to schedule.")
    else:
        used = sum(task.duration_minutes for task in scheduler.planned)
        st.success(
            f"**Today's schedule for {owner.name}:** {len(scheduler.planned)} tasks, "
            f"{used} of {owner.available_minutes} minutes planned."
        )
        conflict_count = len(scheduler.detect_conflicts())
        if conflict_count:
            st.warning(f"⚠️ {conflict_count} time conflict(s) among today's tasks. See the details under Tasks above.")
        if scheduler.planned:
            st.table(
                [
                    {
                        "Time": task.scheduled_time,
                        "Task": task.title,
                        "Pet": task.pet_name,
                        "Minutes": task.duration_minutes,
                        "Priority": task.priority,
                    }
                    for task in scheduler.planned
                ]
            )
            st.caption("Tasks are ordered by priority (high first, then shortest) and run back to back from the start time.")
        if scheduler.skipped:
            st.warning(
                f"**Didn't fit in your {owner.available_minutes} minutes:** "
                + ", ".join(f"{task.title} for {task.pet_name} ({task.duration_minutes} min, {task.priority})" for task in scheduler.skipped)
                + ". Add more time above or lower another task's priority."
            )
        with st.expander("Why this plan?"):
            st.text(scheduler.explain_plan())
