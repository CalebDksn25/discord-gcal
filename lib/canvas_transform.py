from __future__ import annotations
from datetime import datetime, timezone
from dateutil.parser import isoparse

def canvas_assignment_to_task_payload(
    assignment: dict,
    course: dict,
    *,
    use_exact_due_time: bool = True,
) -> dict:
    """
    Returns a dict compatible with your create_task(creds, item) function:
      { "title": str, "due_date": "YYYY-MM-DD" or None, "notes": str or None }

    If use_exact_due_time=True, we’ll keep Canvas due_at time and later set Google due timestamp.
    If False, we’ll only use date (YYYY-MM-DD).
    """

    course_code = course.get("course_code") or course.get("name") or "COURSE"
    name = assignment.get("name") or "Untitled Assignment"
    title = f"{course_code}: {name}"

    due_at = assignment.get("due_at")  # ISO timestamp or None
    due_date = None
    due_rfc3339 = None

    if due_at:
        dt = isoparse(due_at)
        # Canvas usually returns UTC (Z). Ensure timezone-aware.
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # store both: date-only + full timestamp
        due_date = dt.astimezone(timezone.utc).date().isoformat()
        due_rfc3339 = dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    url = assignment.get("html_url")
    points = assignment.get("points_possible")

    notes_lines = []
    if url:
        notes_lines.append(f"Canvas: {url}")
    if points is not None:
        notes_lines.append(f"Points: {points}")
    # Helpful stable identifier for later:
    if assignment.get("id") is not None:
        notes_lines.append(f"canvas_assignment_id: {assignment['id']}")
    if course.get("id") is not None:
        notes_lines.append(f"canvas_course_id: {course['id']}")

    notes = "\n".join(notes_lines) if notes_lines else None

    payload = {
        "type": "task",
        "title": title,
        "start_time": None,
        "end_time": None,
        "due_date": due_date,     # date-only for your existing task creator
        "location": None,
        "notes": notes,
        "assumptions": [],
    }

    # Optional: keep exact due timestamp in notes for now (so you don’t lose it)
    if use_exact_due_time and due_rfc3339:
        payload["assumptions"].append("due_time_from_canvas")
        payload["notes"] = (payload["notes"] or "") + f"\ncanvas_due_rfc3339: {due_rfc3339}"

    return payload