# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "caldav==2.2.3",
#     "icalendar==6.3.2",
#     "langchain-core==1.2.7",
#     "langchain-openai==1.1.7",
#     "langgraph==1.0.7",
#     "marimo>=0.19.0",
#     "python-dotenv==1.2.1",
#     "pytz==2025.2",
#     "pyzmq>=27.1.0",
# ]
# ///
"""LangGraph Agent Demo - Marimo Notebook

A LangGraph-based agent with:
- Email reading tool (GMX)
- Calendar event creation tool (GMX)
- Planning decisions tool
- Show all tools tool
- Memory/conversation history tool
"""

import marimo

__generated_with = "0.19.6"
app = marimo.App(width="columns")


@app.cell(column=0)
def _():
    import marimo as mo
    import os
    from datetime import datetime, timedelta
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

    mo.md("""
    # 🤖 LangGraph Agent Demo

    This demo showcases a LangGraph agent with planning, memory, and custom tools.

    **Features:**
    - 📧 Email reading tool
    - 📅 Calendar event creation tool
    - 🧠 Memory display tool
    - 🔧 Tools introspection
    - 💭 Decision tracking
    """)
    return (
        Calendar,
        ChatOpenAI,
        Event,
        InMemorySaver,
        caldav,
        create_react_agent,
        datetime,
        decode_header,
        email,
        imaplib,
        mo,
        os,
        pytz,
        re,
        timedelta,
        tool,
        uuid,
    )


@app.cell
def _(os):
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
    return (
        GMX_CALDAV_PASSWORD,
        GMX_CALDAV_URL,
        GMX_EMAIL,
        GMX_IMAP_PORT,
        GMX_IMAP_SERVER,
        GMX_PASSWORD,
        agent_state,
    )


@app.cell
def _(mo, os):
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key_status = mo.md("""
        ⚠️ **Warning:** Please set your `OPENAI_API_KEY` in a `.env` file.
        """)
    else:
        api_key_status = mo.md("✅ API Key configured")

    api_key_status
    return


@app.cell
def _(
    GMX_EMAIL,
    GMX_IMAP_PORT,
    GMX_IMAP_SERVER,
    GMX_PASSWORD,
    agent_state,
    datetime,
    decode_header,
    email,
    imaplib,
    re,
    tool,
):
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
    return (read_email,)


@app.cell
def _(
    Calendar,
    Event,
    GMX_CALDAV_PASSWORD,
    GMX_CALDAV_URL,
    GMX_EMAIL,
    agent_state,
    caldav,
    datetime,
    pytz,
    timedelta,
    tool,
    uuid,
):
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
    return (create_calendar_event,)


@app.cell
def _(agent_state, tool):
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
    return (show_decisions,)


@app.cell
def _(agent_state, tool):
    # Tool 4: Memory Display Tool
    @tool
    def show_memory() -> str:
        """Displays the conversation memory/history.
        Use this to show what the agent remembers from previous interactions."""
        output = "💭 Conversation Memory:\n\n"

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
    return (show_memory,)


@app.cell
def _(tool):
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
    return (show_tools,)


@app.cell
def _(
    ChatOpenAI,
    InMemorySaver,
    create_calendar_event,
    create_react_agent,
    os,
    read_email,
    show_decisions,
    show_memory,
    show_tools,
):
    # Create the agent
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

    thread_config = {"configurable": {"thread_id": "marimo-session"}}
    return agent, thread_config


@app.cell
def _(agent_state, mo):
    # Display current state
    mo.md(f"""
    ## 📊 Current State

    - **Emails Read:** {len(agent_state["emails_read"])}
    - **Calendar Events:** {len(agent_state["calendar_events"])}
    - **Decisions Made:** {len(agent_state["decisions"])}
    """)
    return


@app.cell
def _(agent_state, mo):
    # Display calendar events if any
    if agent_state["calendar_events"]:
        events_md = "## 📅 Calendar Events\n\n"
        for event in agent_state["calendar_events"]:
            events_md += f"""
    **{event['title']}**
    - Date: {event['date']}
    - Time: {event['time']}
    - Location: {event['location']}
    - Created: {event['created_at']}

    ---
    """
        calendar_display = mo.md(events_md)
    else:
        calendar_display = mo.md("*No calendar events created yet*")

    calendar_display
    return


@app.cell
def _(agent_state, mo):
    # Display decisions if any
    if agent_state["decisions"]:
        decisions_md = "## 🧠 Agent Decisions\n\n"
        for i, decision in enumerate(agent_state["decisions"], 1):
            decisions_md += f"""
    **{i}. {decision['action']}**
    - Reasoning: {decision['reasoning']}
    - Time: {decision['timestamp']}

    """
        decisions_display = mo.md(decisions_md)
    else:
        decisions_display = mo.md("*No decisions recorded yet*")

    decisions_display
    return


@app.cell(column=1)
def _():
    return


@app.cell
def _(mo):
    mo.md("""
    ## 💬 Chat with the Agent

    **💡 Tip:** Double-Click inside the text area before typing.

    Try these example prompts:
    - "Read my email"
    - "Create a calendar event for dinner tomorrow at 7pm"
    - "Show me your decision-making process"
    - "What tools do you have available?"
    - "Show me the conversation history"
    """)
    return


@app.cell
def _(mo):
    # Create chat input form
    chat_input = mo.ui.text_area(
        placeholder="Ask the agent something... (e.g., 'Read my email')",
        label="Your message:",
        full_width=True
    )

    chat_form = mo.ui.form(
        chat_input,
        submit_button_label="Send"
    )
    chat_form
    return (chat_form,)


@app.cell(column=2)
def _():
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Answers from the LLM
    """)
    return


@app.cell
def _(agent, chat_form, mo, thread_config):
    import traceback

    response_output = mo.md("*Submit a message to see the agent's response*")
    user_message = chat_form.value if chat_form.value is not None else ""

    if user_message:
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_message}]},
                thread_config
            )

            last_message = result["messages"][-1]
            response_text = last_message.content

            response_output = mo.md(f"""
            ### 🤖 Agent Response:

            {response_text}
            """)
        except Exception as e:
            error_details = traceback.format_exc()
            response_output = mo.md(f"""
            ### ❌ Error:

            {str(e)}

            <details>
            <summary>Error details</summary>

            ```
            {error_details}
            ```
            </details>
            """)

    response_output
    return


if __name__ == "__main__":
    app.run()
