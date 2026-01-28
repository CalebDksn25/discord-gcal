from lib.canvas_client import CanvasClient

def list_canvas_courses(canvas_client: CanvasClient) -> list[dict]:
    """List all of the current courses for the user."""
    return canvas_client.get_paginated("/api/v1/courses", params={"enrollment_state": "active", "per_page": 100})