"""
Canvas to Google Tasks sync module.
Handles syncing assignments from Canvas to Google Tasks with deduplication and updating.
"""

import sqlite3
from datetime import datetime
from lib.canvas_client import CanvasClient
from lib.canvas_api import list_active_courses, filter_due_assignments, list_course_assignments
from lib.sync_db import init_db, get_mapping, upsert_mapping
from lib.google_calendar import create_task
from googleapiclient.discovery import build


def build_task_notes(assignment: dict, course: dict) -> str:
    """Build notes field for Google Task from Canvas assignment and course."""
    canvas_url = assignment.get("html_url", "")
    course_name = course.get("name", "Unknown Course")
    course_code = course.get("course_code", "")
    assignment_id = assignment.get("id", "")
    
    notes = f"Canvas Assignment\n"
    if course_code:
        notes += f"Course: {course_code}\n"
    notes += f"Course: {course_name}\n"
    if assignment_id:
        notes += f"Assignment ID: {assignment_id}\n"
    if canvas_url:
        notes += f"URL: {canvas_url}"
    
    return notes


def update_google_task(creds, task_id: str, title: str, due_date: str, notes: str, tasklist_id: str = "@default") -> bool:
    """Update an existing Google Task with new data."""
    try:
        service = build("tasks", "v1", credentials=creds)
        
        task_body = {
            "title": title.strip().title(),
            "notes": notes,
        }
        
        if due_date:
            task_body["due"] = f"{due_date}T23:59:00Z"
        
        service.tasks().update(
            tasklist=tasklist_id,
            task=task_id,
            body=task_body
        ).execute()
        
        return True
    except Exception as e:
        print(f"Error updating Google Task {task_id}: {e}")
        return False


def sync_canvas_assignments_to_google_tasks(
    canvas_client: CanvasClient,
    creds,
    db_path: str = "sync.db",
    tasklist_id: str = "@default"
) -> dict:
    """
    Sync assignments from all Canvas courses to Google Tasks.
    
    Returns:
        dict: Summary with keys: "created", "updated", "skipped", "errors"
    """
    summary = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
    
    # Initialize DB
    conn = init_db(db_path)
    
    try:
        # Get all active courses
        print("Fetching Canvas courses...")
        courses = list_active_courses(canvas_client)
        print(f"Found {len(courses)} active courses")
        
        for course in courses:
            course_id = course.get("id")
            course_name = course.get("name", "Unknown")
            
            try:
                # Get assignments for this course
                print(f"  Syncing {course_name}...")
                assignments = list_course_assignments(canvas_client, course_id)
                
                # Filter to only assignments with due dates
                due_assignments = filter_due_assignments(assignments)
                print(f"    Found {len(due_assignments)} assignments with due dates")
                
                # Sync each assignment
                for assignment in due_assignments:
                    try:
                        assignment_id = assignment.get("id")
                        title = assignment.get("name", "Untitled")
                        due_at = assignment.get("due_at")
                        updated_at = assignment.get("updated_at")
                        
                        # Extract due date (YYYY-MM-DD format)
                        try:
                            due_dt = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
                            due_date = due_dt.strftime("%Y-%m-%d")
                        except:
                            due_date = None
                        
                        # Check if already mapped
                        mapping = get_mapping(conn, assignment_id)
                        
                        if mapping:
                            # Assignment already synced
                            google_task_id, last_canvas_updated_at, last_due_at = mapping
                            
                            # Check if Canvas assignment has been updated since last sync
                            # or if due date changed
                            if updated_at != last_canvas_updated_at or due_date != last_due_at:
                                # Update the Google Task
                                notes = build_task_notes(assignment, course)
                                success = update_google_task(creds, google_task_id, title, due_date, notes, tasklist_id)
                                
                                if success:
                                    upsert_mapping(conn, assignment_id, course_id, google_task_id, updated_at, due_date)
                                    summary["updated"] += 1
                                    print(f"      Updated: {title}")
                                else:
                                    summary["errors"] += 1
                            else:
                                summary["skipped"] += 1
                        else:
                            # New assignment - create Google Task
                            item_dict = {
                                "title": title,
                                "due_date": due_date,
                                "notes": build_task_notes(assignment, course)
                            }
                            
                            try:
                                google_task_id = create_task(creds, item_dict, tasklist_id)
                                upsert_mapping(conn, assignment_id, course_id, google_task_id, updated_at, due_date)
                                summary["created"] += 1
                                print(f"      Created: {title}")
                            except Exception as e:
                                print(f"      Error creating task: {e}")
                                summary["errors"] += 1
                    
                    except Exception as e:
                        print(f"    Error syncing assignment {assignment.get('id')}: {e}")
                        summary["errors"] += 1
            
            except Exception as e:
                print(f"  Error fetching assignments for {course_name}: {e}")
                summary["errors"] += 1
    
    finally:
        conn.close()
    
    return summary
