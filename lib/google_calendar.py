from googleapiclient.discovery import build
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from openai_client import get_date_response

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

def sort_completed_tasks(tasks: list[dict], date) -> list[dict]:
    """Sort tasks by completion date, most recent first."""
   # Separate completed and incomplete tasks, filtering by today's date
    completed = []
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

    return [tasks, completed]

"""
Function that will list task and events for a specific day.
"""
def get_list(creds, calendar_id: str = "primary", tasklist_id: str = "@default", day: str = None) -> dict:
    
    # Default completed array set to nothing
    completed = []

    # If no day is provided, use today's date in Pacific timezone
    pacific = ZoneInfo("America/Los_Angeles")

    # Build the Google calendar and tasks services
    calendar_service = build("calendar", "v3", credentials=creds)
    task_service = build("tasks", "v1", credentials=creds)

    # Define the time range for today using Pacific Time
    pacific = ZoneInfo("America/Los_Angeles")
    now_pacific = datetime.now(pacific)
    date = now_pacific.date()
    start_of_day = datetime.combine(date, datetime.min.time(), tzinfo=pacific).asttimezone(ZoneInfo("UTC")).isoformat().replace('+00:00', 'Z')
    end_of_day = datetime.combine(date, datetime.max.time(), tzinfo=pacific).astimezone(ZoneInfo("UTC")).isoformat().replace('+00:00', 'Z')

    # If there is no specific day, assume today
    if not day:
        # Use todays date
        day = date.isoformat()

        # Fetch todays events and tasks from Google Calendar
        try:

            # Get events for today
            events_result = calendar_service.events().list(
                calendarId=calendar_id,
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            # Get tasks for today
            task_results = task_service.tasks().list(
                tasklist=tasklist_id,
                showCompleted=True,
                showHidden=True
            ).execute()

            # Results from getting items
            events = events_result.get('items', [])
            tasks = task_results.get('items', [])

        except Exception as e:
            print(f"Error fetching calendar events: {e}")
            events = []

    # Use openai to return the correct date format if a specific day is provided
    correct_date = get_date_response(day)

    # Get all tasks and events for the specific day
    try:
        
        # Get events for the specific day
        events_result = calendar_service.events().list(
            calendarId=calendar_id,
            timeMin=f"{correct_date}T00:00:00Z",
            timeMax=f"{correct_date}T23:59:59Z",
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        # Get tasks for the specific day
        task_results = task_service.tasks().list(
            tasklist=tasklist_id,
            showCompleted=True,
            showHidden=True
        ).execute()

        # Results from getting items
        events = events_result.get('items', [])
        tasks = task_results.get('items', [])

        complete_tasks = sort_completed_tasks(tasks, correct_date)
        # Returns [uncompleted array, completed array]

        uncompleted_tasks = complete_tasks[0]
        completed_tasks = complete_tasks[1]

    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        events = []
        uncompleted_tasks = ["error"]
        completed_tasks = ["error"]

    # Return the events and tasks for the day
    return {
        "events": events,
        "tasks": uncompleted_tasks,
        "completed": completed_tasks
    }

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
Function to delete a task by its ID. Returns TRUE if successful.
"""
def delete_task(creds, task_id: str, tasklist_id: str = "@default") -> bool:
    try:
        # Build the google task service
        service = build("tasks", "v1", credentials=creds)

        # Delete the task
        service.tasks().delete(
            tasklist=tasklist_id,
            task=task_id
        ).execute()

        return True

    except Exception as e:
        print(f"Error building Google Tasks service: {e}")
        raise e

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