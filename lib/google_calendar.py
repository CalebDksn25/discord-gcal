from googleapiclient.discovery import build
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

"""
Function to create an event in the google calendar from the item dictionary.
"""
def create_calendar_event(creds, item: dict, calendar_id: str = "primary"):

    # Build the Google Calendar service
    service = build("calendar", "v3", credentials=creds)

    # Create the event body based on the item dictionary
    event = {
        "summary": item["title"].strip().title(),
        "location": item.get("location") or "",
        "description": item.get("notes") or "",
        "start": {"dateTime": item["start_time"]},
        "end": {"dateTime": item["end_time"]},
    }

    # Insert the event into the calendar
    created = service.events().insert(calendarId=calendar_id, body=event).execute()

    # Return the link to the created event
    return created.get('htmlLink')


"""
Function to create a google task from the item dictionary.
"""
def create_task(creds, item: dict, tasklist_id: str = "@default") -> str:

    # Build the Google Tasks service
    service = build("tasks", "v1", credentials=creds)

    # Create the task body based on item dictionary
    task = {
        "title": item["title"].strip().title(),
        "notes": item.get("notes") or "",
    }

    # Google tasks "due" expects RFC3339 Date formate. V1: end-of-day UTC
    if item.get("due_date"):
        task["due"] = f"{item['due_date']}T23:59:00Z"

    # Create the task in the list
    created = service.tasks().insert(tasklist=tasklist_id, body=task).execute()

    # Return the task ID
    return created.get('id')

"""
Function to list all of the current task and events on the users calendar for current day.
"""

def list_today_items(creds, calendar_id: str = "primary", tasklist_id: str = "@default") -> dict:

    # Default completed array set to nothing
    completed = []

    # Build the Google Calendar and Tasks services
    service = build("calendar", "v3", credentials=creds)
    tasks_service = build("tasks", "v1", credentials=creds)

    # Define the time range for today using Pacific timezone
    pacific = ZoneInfo("America/Los_Angeles")
    now_pacific = datetime.now(pacific)
    date = now_pacific.date()
    start_of_day = datetime.combine(date, datetime.min.time(), tzinfo=pacific).astimezone(ZoneInfo("UTC")).isoformat().replace('+00:00', 'Z')
    end_of_day = datetime.combine(date, datetime.max.time(), tzinfo=pacific).astimezone(ZoneInfo("UTC")).isoformat().replace('+00:00', 'Z')

    # Fetch today's events from Google Calendar
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start_of_day,
        timeMax=end_of_day,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    # Fetch today's tasks from Google Tasks
    tomorrow = date + timedelta(days=1)
    
    # Fetch all tasks (completed and hidden included)
    tasks_result = tasks_service.tasks().list(
        tasklist=tasklist_id,
        showCompleted=True,
        showHidden=True
    ).execute()

    tasks = tasks_result.get('items', [])
    
    # Separate completed and incomplete tasks, filtering by today's date
    incomplete_tasks = []
    for task in tasks:
        # Check if task is due today
        task_due = task.get('due')
        is_today = False
        if task_due:
            try:
                # Parse the due date and check if it's today
                task_date = datetime.fromisoformat(task_due.replace('Z', '+00:00')).date()
                is_today = task_date == date
            except:
                pass
        
        # Only include tasks due today
        if is_today:
            if task.get("status") == "completed":
                completed.append(task)
            else:
                incomplete_tasks.append(task)
    
    tasks = incomplete_tasks
    
    # Separate completed and incomplete tasks
    incomplete_tasks = []
    for task in tasks:
        if task.get("status") == "completed":
            completed.append(task)
        else:
            incomplete_tasks.append(task)
    
    tasks = incomplete_tasks
    
    # Return the events and tasks for the day
    return {
        "events": events,
        "tasks": tasks,
        "completed": completed
    }


"""
Function to return open (not completed) tasks from the given task list.
Each item includes id/title/due/notes/updated (when available).
"""
def list_open_tasks(creds, tasklist_id: str = "@default", max_results: int = 100) -> list[dict]:

    # Build the google tasks service
    service = build("tasks", "v1", credentials=creds)

    # Get the response from the tasks list API
    response = service.tasks().list(
        tasklist=tasklist_id,
        showCompleted=False,
        showHidden=False,
        maxResults=max_results
    ).execute()

    # List of the items returned
    items = response.get("items", [])

    # Normalize to have consistent structure
    tasks = []
    for item in items:
        tasks.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "due": item.get("due"),
            "notes": item.get("notes"),
            "updated": item.get("updated"),
        })

    # Return the list of open tasks
    return tasks

"""
Function to mark a task as complete by its ID. Returns TRUE if successful.
"""
def done_task(creds, task_id: str, tasklist_id: str = "@default") -> bool:

    try:
        # Build the Google Tasks service
        service = build("tasks", "v1", credentials=creds)

        # First, get the task to ensure it exists and get its full data
        task = service.tasks().get(
            tasklist=tasklist_id,
            task=task_id
        ).execute()

        # Update the task with completed status
        task["status"] = "completed"
        service.tasks().update(
            tasklist=tasklist_id,
            task=task_id,
            body=task
        ).execute()

        return True

    except Exception as e:
        print(f"Error marking task {task_id} as complete: {e}")
        raise e