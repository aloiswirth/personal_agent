"""Communication Agent - handles email, calendar, and messaging."""

from langchain_core.tools import BaseTool

from src.agents.base import BaseAgent
from .tools import read_email, send_email, create_calendar_event, list_calendar_events


class CommunicationAgent(BaseAgent):
    """Agent for handling communication tasks.
    
    Capabilities:
    - Read and send emails
    - Create and list calendar events
    - (Future) WhatsApp messaging
    """

    def __init__(self):
        super().__init__(
            name="communication",
            description="Handles email, calendar, and messaging tasks",
        )

    @property
    def tools(self) -> list[BaseTool]:
        """Return communication tools."""
        return [
            read_email,
            send_email,
            create_calendar_event,
            list_calendar_events,
        ]

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for the communication agent."""
        return """You are a Communication Assistant that helps manage emails and calendar events.

You have the following capabilities:
1. **read_email**: Read recent emails from the inbox
2. **send_email**: Send emails (not yet implemented)
3. **create_calendar_event**: Create calendar events with title, date, time, location
4. **list_calendar_events**: List upcoming calendar events

Guidelines:
- When reading emails, summarize the key information
- When creating calendar events, confirm all details with the user
- If an email contains event information, offer to create a calendar entry
- Be proactive in suggesting actions based on email content
- Always confirm successful operations

Default behaviors:
- read_email fetches the last 10 emails unless specified otherwise
- list_calendar_events shows the next 7 days unless specified otherwise
- Calendar events default to 1 hour duration"""
