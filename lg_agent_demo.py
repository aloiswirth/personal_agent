"""LangGraph Agent Demo

A LangGraph-based agent with:
- Email reading tool (GMX)
- Calendar event creation tool (GMX)
- Planning decisions tool
- Show all tools tool
- Memory/conversation history tool
"""

import os
from datetime import datetime, timedelta
from typing import Annotated
from dotenv import load_dotenv
import imaplib
import email
from email.header import decode_header
import caldav
from icalendar import Calendar, Event
import pytz
import uuid
import re

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

# Load environment variables
load_dotenv("./.env")

# Configuration
GMX_EMAIL = os.getenv("GMX_EMAIL", "alois_wirth@gmx.de")
GMX_PASSWORD = os.getenv("GMX_PW")
GMX_IMAP_SERVER = os.getenv("GMX_IMAP_SERVER", "imap.gmx.net")
GMX_IMAP_PORT = int(os.getenv("GMX_IMAP_PORT", "993"))
GMX_CALDAV_URL = os.getenv("GMX_CALDAV_URL", f"https://caldav.gmx.net/begenda/dav/{GMX_EMAIL}/calendar/")
GMX_CALDAV_PASSWORD = os.getenv("GMX_KALENDER")

# Global storage for agent state
agent_state = {
    "decisions": [],
    "calendar_events": [],
    "emails_read": [],
}


# Tool 1: Email Reading Tool
@tool
def read_email(count: int = 10) -> str:
    """Reads real emails from GMX account. Use this to retrieve recent email content.
    
    Args:
        count: Number of recent emails to read (default: 10)
    """
    try:
        if not GMX_PASSWORD:
            return "❌ Error: GMX_PW environment variable not set"
        
        mail = imaplib.IMAP4_SSL(GMX_IMAP_SERVER, GMX_IMAP_PORT)
        mail.login(GMX_EMAIL, GMX_PASSWORD)
        mail.select("INBOX")

        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        email_ids = email_ids[-count:]

        result = f"📧 Reading last {len(email_ids)} emails from {GMX_EMAIL}\n\n"
        result += "=" * 80 + "\n\n"

        for email_id in reversed(email_ids):
            status, msg_data = mail.fetch(email_id, "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    subject = msg["Subject"]
                    if subject:
                        decoded_subject = decode_header(subject)[0]
                        if isinstance(decoded_subject[0], bytes):
                            subject = decoded_subject[0].decode(decoded_subject[1] or "utf-8")
                        else:
                            subject = decoded_subject[0]

                    from_addr = msg.get("From", "Unknown")
                    date = msg.get("Date", "Unknown")

                    body = ""
                    body_found = False

                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition", ""))

                            if "attachment" in content_disposition:
                                continue

                            if content_type == "text/plain" and not body_found:
                                try:
                                    payload = part.get_payload(decode=True)
                                    if payload and isinstance(payload, bytes):
                                        charset = part.get_content_charset() or 'utf-8'
                                        body = payload.decode(charset, errors='replace')
                                        body_found = True
                                        break
                                except Exception:
                                    pass

                            elif content_type == "text/html" and not body_found:
                                try:
                                    payload = part.get_payload(decode=True)
                                    if payload and isinstance(payload, bytes):
                                        charset = part.get_content_charset() or 'utf-8'
                                        html_body = payload.decode(charset, errors='replace')
                                        body = re.sub('<[^<]+?>', '', html_body)
                                        body = re.sub(r'\s+', ' ', body).strip()
                                        body_found = True
                                except Exception:
                                    pass
                    else:
                        try:
                            payload = msg.get_payload(decode=True)
                            if payload and isinstance(payload, bytes):
                                charset = msg.get_content_charset() or 'utf-8'
                                body = payload.decode(charset, errors='replace')
                                body_found = True
                        except Exception:
                            try:
                                body = str(msg.get_payload())
                                body_found = True
                            except Exception:
                                body = "Could not decode email body"

                    if not body_found or not body:
                        body = "[No readable content found]"

                    if len(body) > 500:
                        body = body[:500] + "\n... (truncated)"

                    result += f"From: {from_addr}\n"
                    result += f"Subject: {subject}\n"
                    result += f"Date: {date}\n"
                    result += f"\n{body}\n"
                    result += "\n" + "-" * 80 + "\n\n"

        mail.close()
        mail.logout()

        agent_state["emails_read"].append({
            "count": count,
            "timestamp": str(datetime.now())
        })
        agent_state["decisions"].append({
            "action": "read_email",
            "reasoning": f"User requested to read {count} recent emails from GMX",
            "timestamp": str(datetime.now())
        })

        return result

    except Exception as e:
        error_msg = f"❌ Error reading emails: {str(e)}\n\nPlease check your GMX credentials and internet connection."
        agent_state["decisions"].append({
            "action": "read_email_failed",
            "reasoning": f"Failed to read emails: {str(e)}",
            "timestamp": str(datetime.now())
        })
        return error_msg


# Tool 2: Calendar Event Creation Tool
@tool
def create_calendar_event(
    title: str,
    date: str,
    time: str,
    location: str = "",
    description: str = ""
) -> str:
    """Creates a calendar event in GMX calendar with the provided details.
    
    Args:
        title: The title of the event
        date: The date of the event (e.g., 'December 20, 2025' or '2025-12-20')
        time: The time of the event (e.g., '6:00 PM' or '18:00')
        location: The location of the event (optional)
        description: Additional details about the event (optional)
    """
    try:
        from dateutil import parser

        # Parse datetime
        try:
            datetime_str = f"{date} {time}"
            dt = parser.parse(datetime_str)
            if dt.tzinfo is None:
                dt = pytz.timezone('Europe/Berlin').localize(dt)
            start_time = dt
        except Exception:
            now = datetime.now(pytz.timezone('Europe/Berlin'))
            try:
                time_obj = parser.parse(time).time()
                dt = datetime.combine(now.date() + timedelta(days=1), time_obj)
                start_time = pytz.timezone('Europe/Berlin').localize(dt)
            except:
                start_time = datetime.now(pytz.UTC) + timedelta(hours=1)

        end_time = start_time + timedelta(hours=1)

        try:
            client = caldav.DAVClient(
                url=GMX_CALDAV_URL,
                username=GMX_EMAIL,
                password=GMX_CALDAV_PASSWORD
            )
            principal = client.principal()
            calendars = principal.calendars()

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
                cal.add('prodid', '-//LangGraph Agent Demo//CalDAV Client//EN')
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

                event_data = {
                    "title": title,
                    "date": date,
                    "time": time,
                    "location": location,
                    "description": description,
                    "created_at": str(datetime.now()),
                    "synced_to_gmx": True
                }
                agent_state["calendar_events"].append(event_data)

                agent_state["decisions"].append({
                    "action": "create_calendar_event",
                    "reasoning": f"Created event in GMX calendar: {title} on {date} at {time}",
                    "timestamp": str(datetime.now())
                })

                return f"✅ Calendar event created successfully in GMX calendar!\n\nEvent: {title}\nDate: {date}\nTime: {time}\nLocation: {location}\n\n🔗 Synced to your GMX calendar."

        except Exception as caldav_error:
            event_data = {
                "title": title,
                "date": date,
                "time": time,
                "location": location,
                "description": description,
                "created_at": str(datetime.now()),
                "synced_to_gmx": False,
                "sync_error": str(caldav_error)
            }
            agent_state["calendar_events"].append(event_data)

            agent_state["decisions"].append({
                "action": "create_calendar_event_local",
                "reasoning": f"Created event locally (GMX sync failed): {title} on {date} at {time}",
                "timestamp": str(datetime.now())
            })

            return f"✅ Calendar event created locally!\n\nEvent: {title}\nDate: {date}\nTime: {time}\nLocation: {location}\n\n⚠️ Note: Could not sync to GMX calendar. Event stored locally only.\nReason: {str(caldav_error)[:100]}"

    except Exception as e:
        error_msg = f"❌ Error creating calendar event: {str(e)}"
        agent_state["decisions"].append({
            "action": "create_calendar_event_failed",
            "reasoning": f"Failed to create event: {str(e)}",
            "timestamp": str(datetime.now())
        })
        return error_msg


# Tool 3: Decision Display Tool
@tool
def show_decisions() -> str:
    """Displays all decisions and reasoning steps taken by the agent so far.
    Use this to show the agent's thought process."""
    if not agent_state["decisions"]:
        return "No decisions recorded yet."

    output = "🧠 Agent Decisions and Reasoning:\n\n"
    for i, decision in enumerate(agent_state["decisions"], 1):
        output += f"{i}. Action: {decision['action']}\n"
        output += f"   Reasoning: {decision['reasoning']}\n"
        output += f"   Time: {decision['timestamp']}\n\n"
    return output


# Tool 4: Memory Display Tool
@tool
def show_memory() -> str:
    """Displays the conversation memory/history.
    Use this to show what the agent remembers from previous interactions."""
    output = "💭 Conversation Memory:\n\n"
    
    # Show agent state history
    output += "📊 Agent Activity:\n"
    output += f"- Emails Read: {len(agent_state['emails_read'])}\n"
    output += f"- Calendar Events: {len(agent_state['calendar_events'])}\n"
    output += f"- Decisions Made: {len(agent_state['decisions'])}\n\n"
    
    if agent_state["calendar_events"]:
        output += "📅 Calendar Events Created:\n"
        for event in agent_state["calendar_events"]:
            output += f"  - {event['title']} on {event['date']} at {event['time']}\n"
        output += "\n"
    
    if agent_state["emails_read"]:
        output += "📧 Email Reading History:\n"
        for read in agent_state["emails_read"]:
            output += f"  - Read {read['count']} emails at {read['timestamp']}\n"
    
    return output


# Tool 5: Tools Display Tool
@tool
def show_tools() -> str:
    """Displays all available tools and their descriptions.
    Use this to show what capabilities the agent has."""
    tools_info = [
        ("read_email", "Reads real emails from GMX account. Use this to retrieve recent email content."),
        ("create_calendar_event", "Creates a calendar event in GMX calendar with the provided details."),
        ("show_decisions", "Displays all decisions and reasoning steps taken by the agent so far."),
        ("show_memory", "Displays the conversation memory/history."),
        ("show_tools", "Displays all available tools and their descriptions."),
    ]

    output = "🔧 Available Tools:\n\n"
    for i, (name, desc) in enumerate(tools_info, 1):
        output += f"{i}. **{name}**\n"
        output += f"   Description: {desc}\n\n"
    return output


# Create the agent
def create_agent():
    """Create and return the LangGraph agent with memory."""
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.7
    )

    tools = [
        read_email,
        create_calendar_event,
        show_decisions,
        show_memory,
        show_tools
    ]

    checkpointer = InMemorySaver()

    system_prompt = """You are a helpful AI assistant with access to tools for managing emails and calendar events.

You have the following capabilities:
1. Read real emails from GMX account using the read_email tool
2. Create calendar events using the create_calendar_event tool
3. Show your decision-making process using the show_decisions tool
4. Display conversation memory using the show_memory tool
5. List available tools using the show_tools tool

When a user asks you to do something:
1. Think about what tools you need to use
2. Use the tools in a logical order
3. Provide clear feedback about what you're doing

Be proactive and helpful. If you read an email with event details, offer to create a calendar entry for it.

By default, read_email fetches the last 10 emails unless the user specifies a different number."""

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        checkpointer=checkpointer
    )

    return agent, checkpointer


def main():
    """Main function to run the agent interactively."""
    print("🤖 LangGraph Agent Demo")
    print("=" * 50)
    print("\nFeatures:")
    print("- 📧 Email reading tool")
    print("- 📅 Calendar event creation tool")
    print("- 🧠 Memory display tool")
    print("- 🔧 Tools introspection")
    print("- 💭 Decision tracking")
    print("\nType 'quit' or 'exit' to stop.")
    print("=" * 50)

    agent, checkpointer = create_agent()
    thread_id = "main-conversation"
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            print("\n🤖 Agent: ", end="", flush=True)
            
            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config
            )
            
            # Get the last AI message
            last_message = result["messages"][-1]
            print(last_message.content)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
