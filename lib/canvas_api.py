from lib.canvas_client import CanvasClient
from datetime import datetime, timezone

def list_active_courses(canvas_client: CanvasClient) -> list[dict]:
    """List all of the current courses for the user."""
    return canvas_client.get_paginated("/api/v1/courses", params={"enrollment_state": "active", "per_page": 100})

def filter_due_assignments(assignments: list[dict]) -> list[dict]:
    """Filter assignments to only those that have a due date set (and are upcoming)."""
    out = []
    now = datetime.now(timezone.utc)

    for a in assignments:
        due_at = a.get("due_at")
        if not due_at:
            continue

        # If due_at parses as ISO, only keep upcoming
        try:
            due_dt = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
            if due_dt < now:
                continue
        except Exception:
            pass  # if parsing fails, keep it for now

        out.append(a)

    return out

def list_course_assignments(canvas_client: CanvasClient, course_id: int) -> list[dict]:
    """List assignments for a specific course."""
    return canvas_client.get_paginated(
        f"/api/v1/courses/{course_id}/assignments",
        params={"per_page": 100}
    )