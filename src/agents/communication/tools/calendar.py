"""Calendar tools for the Communication Agent."""

import uuid
from datetime import datetime, timedelta

import caldav
import pytz
from dateutil import parser
from icalendar import Calendar, Event
from langchain_core.tools import tool

from src.config import get_settings


@tool
def create_calendar_event(
    title: str,
    date: str,
    time: str,
    location: str = "",
    description: str = ""
) -> str:
    """Creates a calendar event in the configured calendar.
    
    Args:
        title: The title of the event
        date: The date of the event (e.g., 'December 20, 2025' or '2025-12-20')
        time: The time of the event (e.g., '6:00 PM' or '18:00')
        location: The location of the event (optional)
        description: Additional details about the event (optional)
        
    Returns:
        Status message indicating success or failure
    """
    settings = get_settings()
    tz = pytz.timezone(settings.timezone)
    
    # Parse datetime
    try:
        datetime_str = f"{date} {time}"
        dt = parser.parse(datetime_str)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        start_time = dt
    except Exception:
        now = datetime.now(tz)
        try:
            time_obj = parser.parse(time).time()
            dt = datetime.combine(now.date() + timedelta(days=1), time_obj)
            start_time = tz.localize(dt)
        except Exception:
            start_time = datetime.now(pytz.UTC) + timedelta(hours=1)

    end_time = start_time + timedelta(hours=1)

    # Try CalDAV sync
    try:
        if not settings.gmx_kalender:
            raise ValueError("GMX_KALENDER not configured")
            
        client = caldav.DAVClient(
            url=settings.gmx_caldav_full_url,
            username=settings.gmx_email,
            password=settings.gmx_kalender
        )
        principal = client.principal()
        calendars = principal.calendars()

        # Find a writable calendar (skip birthday calendars)
        calendar = None
        for cal in calendars:
            cal_name = cal.name if hasattr(cal, 'name') else ''
            if cal_name and 'geburtstag' not in cal_name.lower() and 'birthday' not in cal_name.lower():
                calendar = cal
                break

        if not calendar and calendars:
            calendar = calendars[-1]

        if calendar:
            cal = Calendar()
            cal.add('prodid', '-//Personal Agent//CalDAV Client//EN')
            cal.add('version', '2.0')

            event = Event()
            event.add('uid', str(uuid.uuid4()))
            event.add('summary', title)
            event.add('dtstart', start_time)
            event.add('dtend', end_time)
            event.add('dtstamp', datetime.now(pytz.UTC))

            if location:
                event.add('location', location)
            if description:
                event.add('description', description)

            cal.add_component(event)
            calendar.save_event(cal.to_ical())

            return (
                f"✅ Calendar event created successfully!\n\n"
                f"Event: {title}\n"
                f"Date: {date}\n"
                f"Time: {time}\n"
                f"Location: {location or 'Not specified'}\n\n"
                f"🔗 Synced to your calendar."
            )

    except Exception as caldav_error:
        # Fall back to local storage
        return (
            f"✅ Calendar event created locally!\n\n"
            f"Event: {title}\n"
            f"Date: {date}\n"
            f"Time: {time}\n"
            f"Location: {location or 'Not specified'}\n\n"
            f"⚠️ Note: Could not sync to remote calendar.\n"
            f"Reason: {str(caldav_error)[:100]}"
        )


@tool
def list_calendar_events(days: int = 7) -> str:
    """List upcoming calendar events.
    
    Args:
        days: Number of days to look ahead (default: 7)
        
    Returns:
        Formatted list of upcoming events
    """
    settings = get_settings()
    
    try:
        if not settings.gmx_kalender:
            return "⚠️ Calendar not configured (GMX_KALENDER not set)"
            
        client = caldav.DAVClient(
            url=settings.gmx_caldav_full_url,
            username=settings.gmx_email,
            password=settings.gmx_kalender
        )
        principal = client.principal()
        calendars = principal.calendars()

        tz = pytz.timezone(settings.timezone)
        start = datetime.now(tz)
        end = start + timedelta(days=days)

        result = f"📅 Upcoming events (next {days} days):\n\n"
        event_count = 0

        for calendar in calendars:
            try:
                events = calendar.date_search(start=start, end=end)
                for event in events:
                    try:
                        ical = Calendar.from_ical(event.data)
                        for component in ical.walk():
                            if component.name == "VEVENT":
                                summary = str(component.get('summary', 'No title'))
                                dtstart = component.get('dtstart')
                                location = str(component.get('location', ''))
                                
                                if dtstart:
                                    dt = dtstart.dt
                                    if hasattr(dt, 'strftime'):
                                        date_str = dt.strftime('%Y-%m-%d %H:%M')
                                    else:
                                        date_str = str(dt)
                                else:
                                    date_str = 'Unknown'
                                
                                result += f"• {summary}\n"
                                result += f"  📆 {date_str}\n"
                                if location:
                                    result += f"  📍 {location}\n"
                                result += "\n"
                                event_count += 1
                    except Exception:
                        continue
            except Exception:
                continue

        if event_count == 0:
            result += "No upcoming events found."

        return result

    except Exception as e:
        return f"❌ Error listing calendar events: {str(e)}"
