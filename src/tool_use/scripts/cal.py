from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.table import Table
from rich import box
import anthropic
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os.path
import pytz
from tzlocal import get_localzone  # Add this import at the top with other imports

client = anthropic.Anthropic()
console = Console()
tool_list =  [
    {
                "name": "create_event",
                "description": "Creates a new calendar event. This tool should be used when the user wants to add a new event to their calendar. It requires a summary (title), start time, and end time. Location and description are optional. The start_time and end_time should be provided in the format YYYY-MM-DD HH:MM. The tool will create the event in the user's primary calendar and return a confirmation message with the event details.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Event title"},
                        "start_time": {"type": "string", "description": "Start time in format YYYY-MM-DD HH:MM"},
                        "end_time": {"type": "string", "description": "End time in format YYYY-MM-DD HH:MM"},
                        "location": {"type": "string", "description": "Event location"},
                        "description": {"type": "string", "description": "Event description"}
                    },
                    "required": ["summary", "start_time", "end_time"]
                }
            },
            {
                "name": "edit_event",
                "description": "Edits an existing calendar event. This tool should be used when the user wants to modify details of an event already in their calendar. It requires the event_id of the event to be edited. The user can update the summary (title), location, or description. The tool will only change the fields provided and leave others unchanged. It will return a confirmation message with the updated event details.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string", "description": "ID of the event to edit"},
                        "summary": {"type": "string", "description": "New event title"},
                        "location": {"type": "string", "description": "New event location"},
                        "description": {"type": "string", "description": "New event description"}
                    },
                    "required": ["event_id"]
                }
            },
            {
                "name": "search_events",
                "description": "Searches for calendar events based on a query. This tool should be used when the user wants to find events in their calendar matching certain criteria. It requires a search query and optionally allows specifying the maximum number of results to return. The tool will search event titles, descriptions, and locations for matches to the query. It returns a list of matching events with their IDs and titles.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Maximum number of results to return"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "delete_event",
                "description": "Deletes a calendar event. This tool should be used when the user wants to remove an event from their calendar. It requires the event_id of the event to be deleted. The tool will permanently remove the specified event from the user's calendar and return a confirmation message. Use this tool with caution as the deletion cannot be undone.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string", "description": "ID of the event to delete"}
                    },
                    "required": ["event_id"]
                }
            },
            {
                "name": "create_multiple_events",
                "description": "Creates multiple calendar events at once. This tool should be used when the user wants to add several events to their calendar in one go. It requires a list of events, where each event has a summary (title), start time, and end time. Location and description are optional for each event. The start_time and end_time should be provided in the format YYYY-MM-DD HH:MM for each event. The tool will create all events in the user's primary calendar and return a confirmation message with details of all created events.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "summary": {"type": "string", "description": "Event title"},
                                    "start_time": {"type": "string", "description": "Start time in format YYYY-MM-DD HH:MM"},
                                    "end_time": {"type": "string", "description": "End time in format YYYY-MM-DD HH:MM"},
                                    "location": {"type": "string", "description": "Event location"},
                                    "description": {"type": "string", "description": "Event description"}
                                },
                                "required": ["summary", "start_time", "end_time"]
                            }
                        }
                    },
                    "required": ["events"]
                }
            },
            {
                "name": "delete_multiple_events",
                "description": "Deletes multiple calendar events at once. This tool should be used when the user wants to remove several events from their calendar in one go. It requires a list of event_ids to be deleted. The tool will permanently remove the specified events from the user's calendar and return a confirmation message. Use this tool with caution as the deletions cannot be undone.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of IDs of the events to delete"
                        }
                    },
                    "required": ["event_ids"]
                }
            },
            {
                "name": "get_free_time",
                "description": "Retrieves free time slots for a given date range. This tool should be used when the user wants to know their available time slots within a specific period. It requires a start date and an end date. Optionally, the user can specify the start and end times for each day. The tool will return a consolidated list of free time slots for each day in the given range.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "Start date in format YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "End date in format YYYY-MM-DD"},
                        "day_start": {"type": "string", "description": "Optional. Start time of day in format HH:MM (24-hour)"},
                        "day_end": {"type": "string", "description": "Optional. End time of day in format HH:MM (24-hour)"}
                    },
                    "required": ["start_date", "end_date"]
                }
            }
]



TIME_ZONE = str(get_localzone())  # Gets the system's local timezone

SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate():
    creds = None
    token_path = 'token.json'
    
    # Check for token.json first
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            if creds and creds.valid:
                return build('calendar', 'v3', credentials=creds)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
                return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            console.print(f"[red]Error with existing token: {str(e)}[/red]")
    
    # If we get here, we either have no token or it's invalid/expired
    console.print(Panel.fit("""
[bold red]No valid authentication token found![/bold red]

To use the calendar features, you need to set up Google Calendar API credentials:

1. Go to [link]https://console.cloud.google.com/[/link]
2. Create a new project or select an existing one
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download the credentials file
6. Copy the contents of the credentials file

Would you like to paste your OAuth credentials now? (y/n)
    """, title="Authentication Required"))
    
    response = Prompt.ask("Enter y/n").lower()
    if response == 'y':
        credentials_json = Prompt.ask("Paste your credentials JSON here")
        try:
            # Save credentials to a temporary file
            with open('credentials_temp.json', 'w') as f:
                f.write(credentials_json)
            
            # Try to authenticate with the provided credentials
            flow = InstalledAppFlow.from_client_secrets_file('credentials_temp.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save the token
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            
            # Clean up temp file
            os.remove('credentials_temp.json')
            
            console.print("[green]Authentication successful![/green]")
            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            console.print(f"[red]Error during authentication: {str(e)}[/red]")
            return None
    else:
        console.print("[yellow]Authentication cancelled. Calendar features will not be available.[/yellow]")
        return None

class CalendarManager:
    def __init__(self, service):
        self.service = service
        self.TIME_ZONE = str(get_localzone())  # Update here as well
    def create_event(self, summary, start_time, end_time, location=None, description=None):
        start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M")  # Remove datetime.
        end_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M")  # Remove datetime.

        event = {
            'summary': summary,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': self.TIME_ZONE,
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': self.TIME_ZONE,
            },
        }

        if location:
            event['location'] = location
        if description:
            event['description'] = description

        event = self.service.events().insert(calendarId='primary', body=event).execute()
        
        table = Table(title="Event Created", box=box.ROUNDED)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Summary", event.get("summary"))
        table.add_row("Start", event["start"]["dateTime"])
        table.add_row("End", event["end"]["dateTime"])
        if location:
            table.add_row("Location", location)
        if description:
            table.add_row("Description", description)
        table.add_row("Link", event.get("htmlLink"))
        
        console.print(table)
        
        return f'Event created: {event.get("summary")} starting at {event["start"]["dateTime"]}. Link: {event.get("htmlLink")}'

    def edit_event(self, event_id, summary=None, location=None, description=None):
        event = self.service.events().get(calendarId='primary', eventId=event_id).execute()

        if summary:
            event['summary'] = summary
        if location:
            event['location'] = location
        if description:
            event['description'] = description

        updated_event = self.service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        
        table = Table(title="Event Updated", box=box.ROUNDED)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Summary", updated_event.get("summary"))
        table.add_row("Start", updated_event["start"]["dateTime"])
        table.add_row("End", updated_event["end"]["dateTime"])
        if location:
            table.add_row("Location", updated_event.get("location"))
        if description:
            table.add_row("Description", updated_event.get("description"))
        table.add_row("Link", updated_event.get("htmlLink"))
        
        console.print(table)
        
        return f'Event updated: {updated_event["htmlLink"]}'

    def search_events(self, query, max_results=10):
        time_min = datetime.utcnow().isoformat() + 'Z'
        events_result = self.service.events().list(calendarId='primary', timeMin=time_min,
                                            maxResults=max_results, singleEvents=True,
                                            orderBy='startTime', q=query).execute()
        events = events_result.get('items', [])

        if not events:
            console.print(Panel("No upcoming events found.", title="Search Results", border_style="yellow"))
            return 'No upcoming events found.'
        
        table = Table(title=f"Search Results for '{query}'", box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Start Time", style="green")
        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            table.add_row(event['id'], event['summary'], start)
        
        console.print(table)
        
        return [{'id': event['id'], 'name': event['summary']} for event in events]

    def delete_event(self, event_id):
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()
        console.print(Panel(f"Event with ID {event_id} has been deleted.", title="Event Deleted", border_style="red"))
        return 'Event deleted'

    def create_multiple_events(self, events):
        created_events = []
        for event_data in events:
            result = self.create_event(**event_data)
            created_events.append(result)
        
        
        for event in created_events:
            parts = event.split(". Link: ")
            if len(parts) == 2:
                summary_and_start, link = parts
                summary, start_time = summary_and_start.split(" starting at ")
                summary = summary.split(": ")[1]  # Remove "Event created: " prefix
        
        return f"{len(created_events)} events created successfully."

    def delete_multiple_events(self, event_ids):
        deleted_events = []
        failed_deletions = []

        for event_id in event_ids:
            try:
                self.service.events().delete(calendarId='primary', eventId=event_id).execute()
                deleted_events.append(event_id)
            except Exception as e:
                failed_deletions.append((event_id, str(e)))

        table = Table(title="Multiple Events Deleted", box=box.ROUNDED)
        table.add_column("Status", style="cyan")
        table.add_column("Event ID", style="magenta")
        table.add_column("Result", style="green")

        for event_id in deleted_events:
            table.add_row("Deleted", event_id, "Success")

        for event_id, error in failed_deletions:
            table.add_row("Failed", event_id, error)

        console.print(table)

        success_count = len(deleted_events)
        fail_count = len(failed_deletions)
        return f"{success_count} events deleted successfully. {fail_count} deletions failed."

    def get_free_time(self, start_date, end_date, day_start='08:00', day_end='22:00'):
        # Convert start_date and end_date to datetime objects
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get the timezone
        timezone = pytz.timezone(self.TIME_ZONE)
        
        free_time = {}

        while start <= end:
            date_str = start.strftime('%Y-%m-%d')
            day_start_time = timezone.localize(datetime.strptime(f"{date_str} {day_start}", '%Y-%m-%d %H:%M'))
            day_end_time = timezone.localize(datetime.strptime(f"{date_str} {day_end}", '%Y-%m-%d %H:%M'))

            # Get events for the day
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=day_start_time.isoformat(),
                timeMax=day_end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            # Initialize free time slots
            free_slots = [(day_start_time, day_end_time)]

            # Adjust free time based on events
            for event in events:
                event_start = self._parse_datetime(event['start'].get('dateTime', event['start'].get('date')))
                event_end = self._parse_datetime(event['end'].get('dateTime', event['end'].get('date')))
                
                new_free_slots = []
                for slot_start, slot_end in free_slots:
                    if event_start <= slot_start and event_end >= slot_end:
                        continue
                    elif event_start > slot_start and event_end < slot_end:
                        new_free_slots.append((slot_start, event_start))
                        new_free_slots.append((event_end, slot_end))
                    elif event_start <= slot_start < event_end:
                        new_free_slots.append((event_end, slot_end))
                    elif event_start < slot_end <= event_end:
                        new_free_slots.append((slot_start, event_start))
                    else:
                        new_free_slots.append((slot_start, slot_end))
                free_slots = new_free_slots

            # Consolidate free time slots
            if free_slots:
                free_time[date_str] = self._consolidate_slots(free_slots)

            start += timedelta(days=1)

        return self._format_free_time(free_time)

    def _consolidate_slots(self, slots):
        consolidated = []
        for slot in sorted(slots):
            if not consolidated or slot[0] - consolidated[-1][1] > timedelta(minutes=30):
                consolidated.append(slot)
            else:
                consolidated[-1] = (consolidated[-1][0], max(consolidated[-1][1], slot[1]))
        return consolidated

    def _format_free_time(self, free_time):
        formatted = []
        for date, slots in free_time.items():
            slot_strs = [f"{slot[0].strftime('%I:%M %p')} to {slot[1].strftime('%I:%M %p')}" for slot in slots]
            formatted.append(f"{date}: {' and '.join(slot_strs)}")
        return '\n'.join(formatted)

    def _parse_datetime(self, dt_string):
        dt = datetime.fromisoformat(dt_string.rstrip('Z'))
        if dt.tzinfo is None:
            return pytz.timezone(self.TIME_ZONE).localize(dt)
        return dt.astimezone(pytz.timezone(self.TIME_ZONE))

# This function creates and returns the CalendarManager instance
def get_calendar_manager():
    service = authenticate()
    if service is None:
        raise Exception("Failed to authenticate with Google Calendar. Please check your credentials and try again.")
    return CalendarManager(service)


def llm(conversation_history):
    now = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

    system_message = f"You are a helpful calendar assistant. You can use these tools to manage the user's calendar: {', '.join([tool['name'] for tool in tool_list])}. If a user doesn't give you enough information, like a start time or end time, you are allowed to make assumptions, and fill in the blanks however you see fit. The user generally does NOT want to be asked for follow up questions, unless absolutely necessary. You can now create and delete multiple events at once using the create_multiple_events and delete_multiple_events tools. Today's date is: {now}."

    while True:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system=system_message,
            messages=conversation_history,
            tool_choice={"type": "auto"},  
            tools=tool_list  
        )
        
        if response.stop_reason == "tool_use":
            for content in response.content:
                if content.type == "text":
                    md = Markdown(content.text)
                    console.print(Panel(md, title="[bold cyan]AI Assistant[/bold cyan]", border_style="cyan", box=box.ROUNDED))
                    console.print()
                if content.type == "tool_use":
                    tool_name = content.name
                    tool_input = content.input
                    tool_use_id = content.id
                    
                    intermediate_result = f"Using tool: {tool_name}\nInput: {tool_input}"
                    md = Markdown(intermediate_result)
                    console.print(Panel(md, title="[bold magenta]Tool Use[/bold magenta]", border_style="magenta", box=box.ROUNDED))
                    console.print()
                    
                    result = execute_tool(tool_name, tool_input)
                    
                    md = Markdown(result)
                    console.print(Panel(md, title="[bold green]Tool Result[/bold green]", border_style="green", box=box.ROUNDED))
                    console.print()
                    
                    conversation_history.append({"role": "assistant", "content": response.content})
                    conversation_history.append({"role": "user", "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result
                        }
                    ]})
            
            # Continue the loop to allow for more tool calls
            continue
        else:
            # If no more tool calls are needed, break the loop
            break
    
    return response.content[0].text if response.content else "I apologize, but I couldn't generate a response."

def execute_tool(tool_name, tool_input):
    calendar_manager = get_calendar_manager()
    if tool_name == "create_event":
        return calendar_manager.create_event(**tool_input)
    elif tool_name == "edit_event":
        return calendar_manager.edit_event(**tool_input)
    elif tool_name == "search_events":
        return calendar_manager.search_events(**tool_input)
    elif tool_name == "delete_event":
        return calendar_manager.delete_event(**tool_input)
    elif tool_name == "create_multiple_events":
        return calendar_manager.create_multiple_events(**tool_input)
    elif tool_name == "delete_multiple_events":
        return calendar_manager.delete_multiple_events(**tool_input)
    elif tool_name == "get_free_time":
        return calendar_manager.get_free_time(**tool_input)
    else:
        return f"Error: Unknown tool '{tool_name}'"

def main(args=None):
    conversation_history = []
    
    print(f"""
          
          
  ___|       |       _)       
 |      _` | |\ \   / | __ \  
 |     (   | | \ \ /  | |   | 
\____|\__,_|_|  \_/  _|_|  _| 
                              
          """)
    
    console.print(Panel.fit("🗓️ [bold cyan]Hi! I'm Calvin, your AI Calendar Assistant! What can I help you with today?[/bold cyan] 🤖", border_style="bold green"))
    
    # Try to authenticate first
    try:
        calendar_manager = get_calendar_manager()
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return
    
    while True:
        user_input = Prompt.ask("\n[bold yellow]You[/bold yellow]")
        if user_input.lower() == 'quit':
            console.print(Panel.fit("[bold red]Goodbye! Have a great day! 👋[/bold red]", border_style="bold red"))
            break
        
        conversation_history.append({"role": "user", "content": user_input})
        
        console.print("\n[bold green]Thinking...[/bold green]")
        response = llm(conversation_history)
        
        conversation_history.append({"role": "assistant", "content": response})
        
        md = Markdown(response)
        console.print(Panel(md, title="[bold cyan]AI Assistant[/bold cyan]", border_style="cyan", box=box.ROUNDED))

if __name__ == '__main__':
    main()

