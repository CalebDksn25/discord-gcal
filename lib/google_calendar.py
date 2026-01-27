from googleapiclient.discovery import build

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
