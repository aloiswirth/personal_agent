"""LangChain Agent Demo with Marimo

This interactive notebook demonstrates a LangChain agent with:
- Planning and decision-making capabilities
- Conversation memory
- Custom tools for email reading and calendar management
- Introspection tools to display agent internals
"""

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
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

    # LangChain imports
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain.memory import ConversationBufferMemory
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.tools import BaseTool
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, AIMessage
    from pydantic import BaseModel, Field

    # Load environment variables
    load_dotenv()

    mo.md("""
    # 🤖 LangChain Agent Demo

    This demo showcases a LangChain agent with planning, memory, and custom tools.

    **Features:**
    - 📧 Email reading tool
    - 📅 Calendar event creation tool
    - 🧠 Memory display tool
    - 🔧 Tools introspection
    - 💭 Decision tracking
    """)
    return (
        AgentExecutor,
        BaseModel,
        BaseTool,
        ChatOpenAI,
        ChatPromptTemplate,
        ConversationBufferMemory,
        Field,
        MessagesPlaceholder,
        Type,
        create_openai_functions_agent,
        datetime,
        mo,
        os,
    )


@app.cell
def _(mo):
    # Configuration section
    mo.md("""
    ## ⚙️ Configuration

    Make sure you have set your `OPENAI_API_KEY` in a `.env` file.
    """)
    return


@app.cell
def _(mo, os):
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        api_key_status = mo.md("""
        ⚠️ **Warning:** Please set your `OPENAI_API_KEY` in a `.env` file.

        Copy `.env.example` to `.env` and add your OpenAI API key.
        """)
    else:
        api_key_status = mo.md("✅ API Key configured")

    api_key_status
    return


@app.cell
def _(os):
    # GMX Email Configuration
    GMX_EMAIL = "alois_wirth@gmx.de"
    GMX_PASSWORD = os.getenv("GMX_PW")
    GMX_IMAP_SERVER = "imap.gmx.net"
    GMX_IMAP_PORT = 993
    
    # GMX CalDAV Configuration
    GMX_CALDAV_URL = f"https://caldav.gmx.net/begenda/dav/{GMX_EMAIL}/calendar/"
    GMX_CALDAV_PASSWORD = os.getenv("GMX_KALENDER")  # App-specific password for calendar
    
    # Global storage for agent state
    agent_state = {
        "decisions": [],
        "calendar_events": [],
        "emails_read": [],
        "memory_history": []
    }
    return GMX_EMAIL, GMX_PASSWORD, GMX_IMAP_SERVER, GMX_IMAP_PORT, GMX_CALDAV_URL, GMX_CALDAV_PASSWORD, agent_state


@app.cell
def _(BaseModel, BaseTool, Field, Type, agent_state, datetime, email, decode_header, imaplib, GMX_EMAIL, GMX_PASSWORD, GMX_IMAP_SERVER, GMX_IMAP_PORT):
    # Tool 1: Email Reading Tool

    class EmailReadInput(BaseModel):
        """Input for reading email."""
        count: int = Field(default=10, description="Number of recent emails to read (default: 10)")

    class EmailReadTool(BaseTool):
        name: str = "read_email"
        description: str = "Reads real emails from GMX account alois_wirth@gmx.de. Use this to retrieve recent email content. By default reads the last 10 emails."
        args_schema: Type[BaseModel] = EmailReadInput

        def _run(self, count: int = 10) -> str:
            """Read real emails from GMX."""
            try:
                # Connect to GMX IMAP server
                mail = imaplib.IMAP4_SSL(GMX_IMAP_SERVER, GMX_IMAP_PORT)
                mail.login(GMX_EMAIL, GMX_PASSWORD)
                mail.select("INBOX")

                # Search for all emails
                status, messages = mail.search(None, "ALL")
                email_ids = messages[0].split()

                # Get the last 'count' emails
                email_ids = email_ids[-count:]
                
                result = f"📧 Reading last {len(email_ids)} emails from {GMX_EMAIL}\n\n"
                result += "=" * 80 + "\n\n"

                for email_id in reversed(email_ids):  # Most recent first
                    # Fetch the email
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            # Decode subject
                            subject = msg["Subject"]
                            if subject:
                                decoded_subject = decode_header(subject)[0]
                                if isinstance(decoded_subject[0], bytes):
                                    subject = decoded_subject[0].decode(decoded_subject[1] or "utf-8")
                                else:
                                    subject = decoded_subject[0]
                            
                            # Get sender
                            from_addr = msg.get("From", "Unknown")
                            
                            # Get date
                            date = msg.get("Date", "Unknown")
                            
                            # Get body - improved extraction
                            body = ""
                            body_found = False
                            
                            if msg.is_multipart():
                                # Walk through all parts to find text content
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    content_disposition = str(part.get("Content-Disposition", ""))
                                    
                                    # Skip attachments
                                    if "attachment" in content_disposition:
                                        continue
                                    
                                    # Try text/plain first
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
                                    
                                    # Fallback to text/html if no text/plain found
                                    elif content_type == "text/html" and not body_found:
                                        try:
                                            payload = part.get_payload(decode=True)
                                            if payload:
                                                charset = part.get_content_charset() or 'utf-8'
                                                html_body = payload.decode(charset, errors='replace')
                                                # Simple HTML tag removal
                                                import re
                                                body = re.sub('<[^<]+?>', '', html_body)
                                                body = re.sub(r'\s+', ' ', body).strip()
                                                body_found = True
                                        except Exception:
                                            pass
                            else:
                                # Single-part message
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
                            
                            # Limit body length for display
                            if len(body) > 500:
                                body = body[:500] + "\n... (truncated)"
                            
                            result += f"From: {from_addr}\n"
                            result += f"Subject: {subject}\n"
                            result += f"Date: {date}\n"
                            result += f"\n{body}\n"
                            result += "\n" + "-" * 80 + "\n\n"

                mail.close()
                mail.logout()

                # Record in agent state
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
            """Async version."""
            return self._run(count)

    email_tool = EmailReadTool()
    return (email_tool,)


@app.cell
def _(BaseModel, BaseTool, Field, Type, agent_state, datetime, timedelta, caldav, Calendar, Event, pytz, GMX_EMAIL, GMX_CALDAV_URL, GMX_CALDAV_PASSWORD):
    # Tool 2: Calendar Event Creation Tool

    class CalendarEventInput(BaseModel):
        """Input for creating a calendar event."""
        title: str = Field(description="The title of the event")
        date: str = Field(description="The date of the event (e.g., 'December 20, 2025' or '2025-12-20')")
        time: str = Field(description="The time of the event (e.g., '6:00 PM' or '18:00')")
        location: str = Field(default="", description="The location of the event")
        description: str = Field(default="", description="Additional details about the event")

    class CalendarEventTool(BaseTool):
        name: str = "create_calendar_event"
        description: str = "Creates a calendar event in GMX calendar with the provided details. Use this to add events to the user's GMX calendar."
        args_schema: Type[BaseModel] = CalendarEventInput

        def _parse_datetime(self, date_str: str, time_str: str) -> datetime:
            """Parse date and time strings into datetime object."""
            from dateutil import parser
            
            # Try to parse the date
            try:
                # Combine date and time
                datetime_str = f"{date_str} {time_str}"
                dt = parser.parse(datetime_str)
                
                # Make timezone aware (use local timezone)
                if dt.tzinfo is None:
                    dt = pytz.timezone('Europe/Berlin').localize(dt)
                
                return dt
            except Exception as e:
                # Fallback: use current date + 1 day at specified time
                now = datetime.now(pytz.timezone('Europe/Berlin'))
                try:
                    time_obj = parser.parse(time_str).time()
                    dt = datetime.combine(now.date() + timedelta(days=1), time_obj)
                    dt = pytz.timezone('Europe/Berlin').localize(dt)
                    return dt
                except:
                    # Last resort: 1 hour from now
                    return datetime.now(pytz.UTC) + timedelta(hours=1)

        def _run(self, title: str, date: str, time: str, location: str = "", description: str = "") -> str:
            """Create a calendar event in GMX calendar."""
            try:
                # Parse datetime
                start_time = self._parse_datetime(date, time)
                end_time = start_time + timedelta(hours=1)  # Default 1 hour duration
                
                # Try to connect to GMX CalDAV
                try:
                    client = caldav.DAVClient(
                        url=GMX_CALDAV_URL,
                        username=GMX_EMAIL,
                        password=GMX_CALDAV_PASSWORD
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
                        calendar = calendars[-1]  # Use last calendar as fallback
                    
                    if calendar:
                        # Create iCalendar event with all required fields
                        cal = Calendar()
                        
                        # Add required calendar properties
                        cal.add('prodid', '-//LangChain Agent Demo//CalDAV Client//EN')
                        cal.add('version', '2.0')
                        
                        event = Event()
                        
                        # Generate unique UID (required)
                        import uuid
                        event.add('uid', str(uuid.uuid4()))
                        
                        # Add event properties
                        event.add('summary', title)
                        event.add('dtstart', start_time)
                        event.add('dtend', end_time)
                        event.add('dtstamp', datetime.now(pytz.UTC))  # Required: timestamp of creation
                        
                        if location:
                            event.add('location', location)
                        if description:
                            event.add('description', description)
                        
                        cal.add_component(event)
                        
                        # Save to CalDAV server
                        calendar.save_event(cal.to_ical())
                        
                        # Also store locally
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
                    # CalDAV failed, store locally only
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
            """Async version."""
            return self._run(title, date, time, location, description)

    calendar_tool = CalendarEventTool()
    return (calendar_tool,)


@app.cell
def _(BaseModel, BaseTool, Type, agent_state):
    # Tool 3: Decision Display Tool

    class DecisionDisplayInput(BaseModel):
        """Input for displaying decisions."""
        pass

    class DecisionDisplayTool(BaseTool):
        name: str = "show_decisions"
        description: str = "Displays all decisions and reasoning steps taken by the agent so far. Use this to show the agent's thought process."
        args_schema: Type[BaseModel] = DecisionDisplayInput

        def _run(self) -> str:
            """Display all decisions."""
            if not agent_state["decisions"]:
                return "No decisions recorded yet."

            output = "🧠 Agent Decisions and Reasoning:\n\n"
            for i, decision in enumerate(agent_state["decisions"], 1):
                output += f"{i}. Action: {decision['action']}\n"
                output += f"   Reasoning: {decision['reasoning']}\n"
                output += f"   Time: {decision['timestamp']}\n\n"
            return output

        async def _arun(self) -> str:
            """Async version."""
            return self._run()

    decision_tool = DecisionDisplayTool()
    return (decision_tool,)


@app.cell
def _(BaseModel, BaseTool, Type, agent_state):
    # Tool 4: Memory Display Tool

    class MemoryDisplayInput(BaseModel):
        """Input for displaying memory."""
        pass

    class MemoryDisplayTool(BaseTool):
        name: str = "show_memory"
        description: str = "Displays the conversation memory/history. Use this to show what the agent remembers from previous interactions."
        args_schema: Type[BaseModel] = MemoryDisplayInput

        def _run(self) -> str:
            """Display conversation memory."""
            if not agent_state["memory_history"]:
                return "No conversation history yet."

            output = "💭 Conversation Memory:\n\n"
            for i, entry in enumerate(agent_state["memory_history"], 1):
                output += f"{i}. {entry['role']}: {entry['content'][:100]}...\n"
                output += f"   Time: {entry['timestamp']}\n\n"
            return output

        async def _arun(self) -> str:
            """Async version."""
            return self._run()

    memory_tool = MemoryDisplayTool()
    return (memory_tool,)


@app.cell
def _(
    BaseModel,
    BaseTool,
    Type,
    calendar_tool,
    decision_tool,
    email_tool,
    memory_tool,
):
    # Tool 5: Tools Display Tool

    class ToolsDisplayInput(BaseModel):
        """Input for displaying available tools."""
        pass

    class ToolsDisplayTool(BaseTool):
        name: str = "show_tools"
        description: str = "Displays all available tools and their descriptions. Use this to show what capabilities the agent has."
        args_schema: Type[BaseModel] = ToolsDisplayInput

        def _run(self) -> str:
            """Display all available tools."""
            tools_list = [email_tool, calendar_tool, decision_tool, memory_tool]

            output = "🔧 Available Tools:\n\n"
            for i, tool in enumerate(tools_list, 1):
                output += f"{i}. **{tool.name}**\n"
                output += f"   Description: {tool.description}\n\n"
            return output

        async def _arun(self) -> str:
            """Async version."""
            return self._run()

    tools_display_tool = ToolsDisplayTool()
    return (tools_display_tool,)


@app.cell
def _(
    AgentExecutor,
    ChatOpenAI,
    ChatPromptTemplate,
    ConversationBufferMemory,
    MessagesPlaceholder,
    calendar_tool,
    create_openai_functions_agent,
    decision_tool,
    email_tool,
    memory_tool,
    os,
    tools_display_tool,
):
    # Initialize LLM
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.7
    )

    # Combine all tools
    tools = [
        email_tool,
        calendar_tool,
        decision_tool,
        memory_tool,
        tools_display_tool
    ]

    # Create memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful AI assistant with access to tools for managing emails and calendar events.

    You have the following capabilities:
    1. Read real emails from GMX account (alois_wirth@gmx.de) using the read_email tool
    2. Create calendar events using the create_calendar_event tool
    3. Show your decision-making process using the show_decisions tool
    4. Display conversation memory using the show_memory tool
    5. List available tools using the show_tools tool

    When a user asks you to do something:
    1. Think about what tools you need to use
    2. Use the tools in a logical order
    3. Provide clear feedback about what you're doing

    Be proactive and helpful. If you read an email with event details, offer to create a calendar entry for it.
    
    By default, read_email fetches the last 10 emails unless the user specifies a different number."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create agent
    agent = create_openai_functions_agent(llm, tools, prompt)

    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10
    )
    return (agent_executor,)


@app.cell
def _(mo):
    mo.md("""
    ## 💬 Chat with the Agent

    **💡 Tip:** Double-Click inside the text area before typing to avoid triggering marimo keyboard shortcuts.

    Try these example prompts:
    - "Read my email"
    - "Create a calendar event for the birthday party"
    - "Show me your decision-making process"
    - "What tools do you have available?"
    - "Show me the conversation history"
    """)
    return


@app.cell
def _(mo):
    # Create a form that properly handles submission in marimo
    # Using mo.ui.form ensures the button click triggers reactivity
    chat_input = mo.ui.text_area(
        placeholder="Ask the agent something... (e.g., 'Read my email and create a calendar event')",
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
    # Diagnostic cell to output form value
    mo.md(f"""
    ### 🔍 Debug: Form Value

    **chat_form.value:** `{repr(chat_form.value)}`

    **Type:** `{type(chat_form.value)}`

    **Is submitted:** `{chat_form.value is not None}`
    """)
    return


@app.cell
def _(agent_executor, agent_state, chat_form, datetime, mo):
    # Process user input and display response
    import traceback

    # Initialize default response
    response_output = mo.md("*Submit a message to see the agent's response*")
    result = None
    response_text = ""

    # Get the user input value from the form
    # When form is submitted, chat_form.value contains the text area value directly
    user_message = chat_form.value if chat_form.value is not None else ""

    # Check if form was submitted and there's input
    if user_message:
        # Record in memory history
        agent_state["memory_history"].append({
            "role": "Human",
            "content": user_message,
            "timestamp": str(datetime.now())
        })

        # Run the agent
        try:
            result = agent_executor.invoke({"input": user_message})
            response_text = result.get("output", "No response generated.")

            # Record agent response in memory history
            agent_state["memory_history"].append({
                "role": "AI",
                "content": response_text,
                "timestamp": str(datetime.now())
            })

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

            Please check your API key and try again.
            """)

    response_output
    return


@app.cell
def _(agent_state, mo):
    # Display current state
    mo.md(f"""
    ## 📊 Current State

    - **Emails Read:** {len(agent_state["emails_read"])}
    - **Calendar Events:** {len(agent_state["calendar_events"])}
    - **Decisions Made:** {len(agent_state["decisions"])}
    - **Conversation Turns:** {len(agent_state["memory_history"])}
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
def _(mo):
    mo.md("""
    ## 🎯 Demo Instructions

    1. **Start simple:** Ask the agent to "Read my email"
    2. **Create an event:** Ask it to "Create a calendar event for the birthday party"
    3. **Inspect internals:** Try "Show me your decisions" or "Show me the conversation history"
    4. **Explore tools:** Ask "What tools do you have?"

    The agent will use its planning capabilities to decide which tools to use and in what order!
    """)
    return


if __name__ == "__main__":
    app.run()
