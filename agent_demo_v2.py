# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "caldav==2.2.3",
#     "icalendar==6.3.2",
#     "marimo>=0.19.0",
#     "pydantic==2.12.5",
#     "python-dotenv==1.2.1",
#     "pytz==2025.2",
#     "pyzmq>=27.1.0",
# ]
# ///

import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell
def _():
    """LangChain-free Agent Demo v2 with Marimo

    This reworked notebook avoids deprecated LangChain internals and implements
    a lightweight, deterministic agent controller that calls the previously
    implemented tools (email reading, calendar creation, introspection).

    Notes:
    - To keep compatibility with newer LangChain versions, this file does not
      depend on langchain agent classes or prompt helpers.
    - The "agent" behavior is a small rule-based dispatcher that recognizes a
      few commands and also supports simple structured commands for creating
      events or reading a specific number of emails.
    - Main functionality (read emails, create calendar events, show decisions,
      show memory, list tools) is preserved.

    Usage examples (type into the chat):
    - "Read my email"
    - "read_email|5"        -> reads last 5 emails
    - "Create an event"    -> the assistant will ask for structured input
    - "create_event|Title|2025-12-20|18:00|Location|Description"
    - "Show me your decisions"
    - "Show me the conversation history"
    - "What tools do you have?"
    """
    import marimo as mo
    from pydantic import BaseModel, Field
    import os
    from datetime import datetime, timedelta
    from typing import Optional, Type, List, Dict, Any
    from dotenv import load_dotenv
    import imaplib
    import email
    from email.header import decode_header
    import caldav
    from icalendar import Calendar, Event
    import pytz
    import re

    # Load environment variables
    load_dotenv("./.env")

    # Config
    GMX_EMAIL = os.getenv("GMX_EMAIL", "alois_wirth@gmx.de")
    GMX_PASSWORD = os.getenv("GMX_PW")
    GMX_IMAP_SERVER = os.getenv("GMX_IMAP_SERVER", "imap.gmx.net")
    GMX_IMAP_PORT = int(os.getenv("GMX_IMAP_PORT", "993"))
    GMX_CALDAV_URL = os.getenv("GMX_CALDAV_URL", f"https://caldav.gmx.net/begenda/dav/{GMX_EMAIL}/calendar/")
    GMX_CALDAV_PASSWORD = os.getenv("GMX_KALENDER")

    # Simple in-memory agent state
    agent_state: Dict[str, Any] = {
        "emails_read": [],
        "calendar_events": [],
        "decisions": [],
        "memory_history": []
    }

    mo.md("""
    # 🤖 Agent Demo v2 (LangChain-free)

    This demo keeps the original tools but avoids relying on LangChain
    agent internals that may be removed in newer LangChain releases.

    **Features:**
    - 📧 Email reading tool
    - 📅 Calendar event creation tool
    - 🧠 Memory display tool
    - 🔧 Tools introspection
    - 💭 Decision tracking
    """)
    return (
        BaseModel,
        Calendar,
        Event,
        Field,
        GMX_CALDAV_PASSWORD,
        GMX_CALDAV_URL,
        GMX_EMAIL,
        GMX_IMAP_PORT,
        GMX_IMAP_SERVER,
        GMX_PASSWORD,
        Type,
        agent_state,
        caldav,
        datetime,
        decode_header,
        email,
        imaplib,
        mo,
        pytz,
        re,
        timedelta,
    )


@app.cell
def _(
    BaseModel,
    Field,
    GMX_EMAIL,
    GMX_IMAP_PORT,
    GMX_IMAP_SERVER,
    GMX_PASSWORD,
    Type,
    agent_state: "Dict[str, Any]",
    datetime,
    decode_header,
    email,
    imaplib,
):
    # Email reading tool (keeps original behavior but does not inherit from langchain BaseTool)
    class EmailReadInput(BaseModel):
        count: int = Field(default=10, description="Number of recent emails to read (default: 10)")

    class EmailReadTool:
        name: str = "read_email"
        description: str = (
            "Reads real emails from GMX account. Use this to retrieve recent email content. "
            "By default reads the last 10 emails."
        )
        args_schema: Type[BaseModel] = EmailReadInput

        def _run(self, count: int = 10) -> str:
            try:
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
                            subject = msg.get("Subject")
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
                                            if payload:
                                                charset = part.get_content_charset() or 'utf-8'
                                                body = payload.decode(charset, errors='replace')
                                                body_found = True
                                                break
                                        except Exception:
                                            pass

                                    elif content_type == "text/html" and not body_found:
                                        try:
                                            payload = part.get_payload(decode=True)
                                            if payload:
                                                charset = part.get_content_charset() or 'utf-8'
                                                html_body = payload.decode(charset, errors='replace')
                                                import re as regex
                                                body = regex.sub('<[^<]+?>', '', html_body)
                                                body = regex.sub(r'\s+', ' ', body).strip()
                                                body_found = True
                                        except Exception:
                                            pass
                            else:
                                try:
                                    payload = msg.get_payload(decode=True)
                                    if payload:
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

        async def _arun(self, count: int = 10) -> str:
            return self._run(count)

    email_tool = EmailReadTool()
    return (email_tool,)


@app.cell
def _(
    BaseModel,
    Calendar,
    Event,
    Field,
    GMX_CALDAV_PASSWORD,
    GMX_CALDAV_URL,
    GMX_EMAIL,
    Type,
    agent_state: "Dict[str, Any]",
    caldav,
    datetime,
    pytz,
    timedelta,
):
    # Calendar creation tool (keeps original behavior)
    class CalendarEventInput(BaseModel):
        title: str = Field(description="The title of the event")
        date: str = Field(description="The date of the event (e.g., 'December 20, 2025' or '2025-12-20')")
        time: str = Field(description="The time of the event (e.g., '6:00 PM' or '18:00')")
        location: str = Field(default="", description="The location of the event")
        description: str = Field(default="", description="Additional details about the event")

    class CalendarEventTool:
        name: str = "create_calendar_event"
        description: str = "Creates a calendar event in GMX calendar with the provided details."
        args_schema: Type[BaseModel] = CalendarEventInput

        def _parse_datetime(self, date_str: str, time_str: str) -> datetime:
            try:
                from dateutil import parser
                datetime_str = f"{date_str} {time_str}"
                dt = parser.parse(datetime_str)
                if dt.tzinfo is None:
                    dt = pytz.timezone('Europe/Berlin').localize(dt)
                return dt
            except Exception:
                now = datetime.now(pytz.timezone('Europe/Berlin'))
                try:
                    from dateutil import parser
                    time_obj = parser.parse(time_str).time()
                    dt = datetime.combine(now.date() + timedelta(days=1), time_obj)
                    dt = pytz.timezone('Europe/Berlin').localize(dt)
                    return dt
                except Exception:
                    return datetime.now(pytz.UTC) + timedelta(hours=1)

        def _run(self, title: str, date: str, time: str, location: str = "", description: str = "") -> str:
            try:
                start_time = self._parse_datetime(date, time)
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
                        cal.add('prodid', '-//Agent Demo v2//CalDAV Client//EN')
                        cal.add('version', '2.0')

                        event = Event()
                        import uuid
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

                    # If no calendar found but no exception occurred, fall back to storing locally
                    event_data = {
                        "title": title,
                        "date": date,
                        "time": time,
                        "location": location,
                        "description": description,
                        "created_at": str(datetime.now()),
                        "synced_to_gmx": False,
                        "sync_error": "No writable calendar found"
                    }
                    agent_state["calendar_events"].append(event_data)

                    agent_state["decisions"].append({
                        "action": "create_calendar_event_local",
                        "reasoning": f"Created event locally (no calendar available): {title} on {date} at {time}",
                        "timestamp": str(datetime.now())
                    })

                    return f"✅ Calendar event created locally!\n\nEvent: {title}\nDate: {date}\nTime: {time}\nLocation: {location}\n\n⚠️ Note: No writable calendar found on GMX. Event stored locally only."

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

        async def _arun(self, title: str, date: str, time: str, location: str = "", description: str = "") -> str:
            return self._run(title, date, time, location, description)

    calendar_tool = CalendarEventTool()
    return (calendar_tool,)


@app.cell
def _(agent_state: "Dict[str, Any]"):
    class DecisionDisplayTool:
        name: str = "show_decisions"
        description: str = "Displays all decisions and reasoning steps taken by the agent so far."

        def _run(self) -> str:
            if not agent_state["decisions"]:
                return "No decisions recorded yet."
            output = "🧠 Agent Decisions and Reasoning:\n\n"
            for i, decision in enumerate(agent_state["decisions"], 1):
                output += f"{i}. Action: {decision['action']}\n"
                output += f"   Reasoning: {decision['reasoning']}\n"
                output += f"   Time: {decision['timestamp']}\n\n"
            return output

        async def _arun(self) -> str:
            return self._run()

    decision_tool = DecisionDisplayTool()
    return (decision_tool,)


@app.cell
def _(agent_state: "Dict[str, Any]"):
    class MemoryDisplayTool:
        name: str = "show_memory"
        description: str = "Displays the conversation memory/history."

        def _run(self) -> str:
            if not agent_state["memory_history"]:
                return "No conversation history yet."
            output = "💭 Conversation Memory:\n\n"
            for i, entry in enumerate(agent_state["memory_history"], 1):
                content_preview = entry['content'][:100] + ("..." if len(entry['content'])>100 else "")
                output += f"{i}. {entry['role']}: {content_preview}\n"
                output += f"   Time: {entry['timestamp']}\n\n"
            return output

        async def _arun(self) -> str:
            return self._run()

    memory_tool = MemoryDisplayTool()
    return (memory_tool,)


@app.cell
def _(calendar_tool, decision_tool, email_tool, memory_tool):
    class ToolsDisplayTool:
        name: str = "show_tools"
        description: str = "Displays all available tools and their descriptions."

        def _run(self) -> str:
            tools_list = [email_tool, calendar_tool, decision_tool, memory_tool]
            output = "🔧 Available Tools:\n\n"
            for i, tool in enumerate(tools_list, 1):
                output += f"{i}. {tool.name}\n"
                output += f"   Description: {tool.description}\n\n"
            return output

        async def _arun(self) -> str:
            return self._run()

    tools_display_tool = ToolsDisplayTool()
    return (tools_display_tool,)


@app.cell
def _(mo):
    mo.md("""
    ## 💬 Chat with the Agent

    Type plain language commands like "Read my email" or use the quick structured
    commands to guarantee action:

    - read_email|<count>  (e.g. read_email|5)
    - create_event|Title|YYYY-MM-DD|HH:MM|Location|Description

    The small dispatcher below will map your message to tool calls.
    """)
    return


@app.cell
def _(mo):
    chat_input = mo.ui.text_area(
        placeholder="Ask the agent something... (e.g., 'Read my email' or 'create_event|...')",
        label="Your message:",
        full_width=True
    )

    chat_form = mo.ui.form(
        chat_input,
        submit_button_label="Send"
    )
    chat_form
    return (chat_form,)


@app.cell
def _(chat_form, mo):
    mo.md(f"""
    ### 🔍 Debug: Form Value

    **chat_form.value:** `{repr(chat_form.value)}`

    **Type:** `{type(chat_form.value)}`

    **Is submitted:** `{chat_form.value is not None}`
    """)
    return


@app.cell
def _(
    agent_state: "Dict[str, Any]",
    calendar_tool,
    chat_form,
    datetime,
    decision_tool,
    email_tool,
    memory_tool,
    mo,
    re,
    tools_display_tool,
):
    import traceback

    response_output = mo.md("*Submit a message to see the agent's response*")

    user_message = chat_form.value if chat_form.value is not None else ""

    if user_message:
        agent_state["memory_history"].append({
            "role": "Human",
            "content": user_message,
            "timestamp": str(datetime.now())
        })

        try:
            text = user_message.strip().lower()

            # Structured: read_email|N
            if text.startswith("read_email|"):
                try:
                    count = int(user_message.split("|", 1)[1])
                except Exception:
                    count = 10
                result = email_tool._run(count=count)
                agent_state["memory_history"].append({"role": "AI", "content": result, "timestamp": str(datetime.now())})
                response_output = mo.md(f"### 🤖 Agent Response:\n\n{result}")

            # Structured: create_event|Title|date|time|location|description
            elif text.startswith("create_event|"):
                parts = user_message.split("|")
                if len(parts) >= 4:
                    title = parts[1].strip()
                    date = parts[2].strip()
                    time = parts[3].strip()
                    location = parts[4].strip() if len(parts) > 4 else ""
                    description = parts[5].strip() if len(parts) > 5 else ""
                    result = calendar_tool._run(title=title, date=date, time=time, location=location, description=description)
                    agent_state["memory_history"].append({"role": "AI", "content": result, "timestamp": str(datetime.now())})
                    response_output = mo.md(f"### 🤖 Agent Response:\n\n{result}")
                else:
                    msg = ("To create an event, use the structured form:\n"
                           "create_event|Title|YYYY-MM-DD|HH:MM|Location|Description")
                    response_output = mo.md(msg)

            # Intent: create in plain language -> ask for structured command
            elif any(k in text for k in ("create event", "create calendar", "add event", "schedule")):
                msg = ("I can create a calendar event for you. Please provide details in this structured format:\n"
                       "create_event|Title|YYYY-MM-DD|HH:MM|Location|Description\n\n"
                       "Example: create_event|Birthday Party|2025-12-20|18:00|My House|Bring cake")
                response_output = mo.md(msg)

            # Read email in plain language
            elif any(k in text for k in ("read my email", "read email", "emails")):
                # try to extract a number like "last 5 emails"
                m = re.search(r"(\d+)", user_message)
                count = int(m.group(1)) if m else 10
                result = email_tool._run(count=count)
                agent_state["memory_history"].append({"role": "AI", "content": result, "timestamp": str(datetime.now())})
                response_output = mo.md(f"### 🤖 Agent Response:\n\n{result}")

            # Show decisions
            elif any(k in text for k in ("show decisions", "decisions")):
                result = decision_tool._run()
                response_output = mo.md(f"### �� Agent Response:\n\n{result}")

            # Show memory
            elif any(k in text for k in ("show memory", "conversation history", "history")):
                result = memory_tool._run()
                response_output = mo.md(f"### 🤖 Agent Response:\n\n{result}")

            # Show tools
            elif any(k in text for k in ("what tools", "show tools", "tools")):
                result = tools_display_tool._run()
                response_output = mo.md(f"### 🤖 Agent Response:\n\n{result}")

            else:
                # Fallback: simple canned reply encouraging supported commands
                fallback = (
                    "I didn't fully understand. Try one of the supported commands:\n"
                    "- read_email|5  (reads last 5 emails)\n"
                    "- create_event|Title|YYYY-MM-DD|HH:MM|Location|Description\n"
                    "- show_decisions\n"
                    "- show_memory\n"
                    "- show_tools\n\n"
                    "Or ask clearly: 'Read my email' or 'Create a calendar event'."
                )
                response_output = mo.md(f"### 🤖 Agent Response:\n\n{fallback}")

        except Exception as e:
            tb = traceback.format_exc()
            response_output = mo.md(f"### ❌ Error:\n\n{str(e)}\n\n<details>\n<summary>Error details</summary>\n\n```\n{tb}\n```\n</details>")

    response_output
    return


@app.cell
def _(agent_state: "Dict[str, Any]", mo):
    mo.md(f"""
    ## 📊 Current State

    - **Emails Read:** {len(agent_state["emails_read"])}
    - **Calendar Events:** {len(agent_state["calendar_events"])}
    - **Decisions Made:** {len(agent_state["decisions"])}
    - **Conversation Turns:** {len(agent_state["memory_history"])}
    """)
    return


@app.cell
def _(agent_state: "Dict[str, Any]", mo):
    if agent_state["calendar_events"]:
        events_md = "## 📅 Calendar Events\n\n"
        for event in agent_state["calendar_events"]:
            events_md += f"**{event['title']}**\n- Date: {event['date']}\n- Time: {event['time']}\n- Location: {event['location']}\n- Created: {event['created_at']}\n\n---\n\n"
        calendar_display = mo.md(events_md)
    else:
        calendar_display = mo.md("*No calendar events created yet*")

    calendar_display
    return


@app.cell
def _(mo):
    mo.md("""
    ## 🎯 Demo Instructions

    Use the quick structured commands for predictable results:
    - read_email|<count>
    - create_event|Title|YYYY-MM-DD|HH:MM|Location|Description

    Or type plain language requests such as "Read my email".
    """)
    return


if __name__ == "__main__":
    app.run()
