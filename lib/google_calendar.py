from googleapiclient.discovery import build
from datetime import datetime, timedelta

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

    # Define the time range for today
    date = datetime.utcnow().date()
    start_of_day = datetime.combine(date, datetime.min.time()).isoformat() + 'Z'  # 'Z' indicates UTC time
    end_of_day = datetime.combine(date, datetime.max.time()).isoformat() + 'Z'

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
    # Note: Google Tasks uses date-only format for 'due' field, so we need to use date strings
    # dueMin is inclusive, dueMax is exclusive, so we need to set dueMax to tomorrow
    tomorrow = date + timedelta(days=1)
    tasks_result = tasks_service.tasks().list(
        tasklist=tasklist_id,
        showCompleted=True,
        showHidden=True,
        dueMax=tomorrow.isoformat() + 'T00:00:00Z',  # Up to (but not including) tomorrow
        dueMin=start_of_day  # From start of today
    ).execute()

    tasks = tasks_result.get('items', [])
    print("Fetched tasks:", len(tasks), "items")
    
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
