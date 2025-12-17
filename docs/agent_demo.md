# agent_demo.py Documentation

## Purpose
Interactive Marimo notebook demonstrating a LangChain agent with real email reading capabilities from GMX, calendar management, conversation memory, and introspection tools.

## Features
- **Real Email Reading**: Connects to GMX IMAP server to fetch actual emails from alois_wirth@gmx.de
- **GMX Calendar Integration**: Creates calendar events in GMX calendar via CalDAV (with local fallback)
- **Conversation Memory**: Maintains conversation history across interactions
- **Decision Tracking**: Records and displays agent's decision-making process
- **Tool Introspection**: Shows available tools and their capabilities

## Usage

### Running the Application
```bash
marimo edit agent_demo.py
```

### Environment Variables Required
Create a `.env` file with:
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
GMX_PW=your_gmx_password_here
GMX_KALENDER=your_gmx_app_specific_password_here  # For CalDAV calendar access
```

**Note**: Generate the GMX_KALENDER app-specific password in your GMX account settings under Security > App Passwords.

### Example Prompts
- "Read my email" - Fetches the last 10 emails from GMX
- "Read my last 5 emails" - Fetches the last 5 emails
- "Create a calendar event for [event details]"
- "Show me your decision-making process"
- "What tools do you have available?"
- "Show me the conversation history"

## Components

### Email Reading Tool
- **Name**: `read_email`
- **Description**: Reads real emails from GMX account alois_wirth@gmx.de
- **Parameters**:
  - `count` (int, default=10): Number of recent emails to read
- **Functionality**:
  - Connects to GMX IMAP server (imap.gmx.net:993)
  - Authenticates using credentials from .env file
  - Fetches the most recent N emails from INBOX
  - Decodes email headers and body content
  - Displays: From, Subject, Date, and Body (truncated to 500 chars)
  - Returns formatted email list with separators

### Calendar Event Tool
- **Name**: `create_calendar_event`
- **Description**: Creates calendar events in GMX calendar with provided details
- **Parameters**:
  - `title` (str, required): Event title
  - `date` (str, required): Event date (e.g., 'December 20, 2025' or '2025-12-20')
  - `time` (str, required): Event time (e.g., '6:00 PM' or '18:00')
  - `location` (str, optional): Event location
  - `description` (str, optional): Additional details
- **Functionality**:
  - Attempts to create event in GMX calendar via CalDAV
  - Falls back to local storage if CalDAV sync fails
  - Parses flexible date/time formats using dateutil
  - Sets default 1-hour duration
  - Uses Europe/Berlin timezone
  - Skips read-only calendars (e.g., birthday calendars)

### Decision Display Tool
- **Name**: `show_decisions`
- **Description**: Displays all decisions and reasoning steps taken by the agent
- **Functionality**: Shows action, reasoning, and timestamp for each decision

### Memory Display Tool
- **Name**: `show_memory`
- **Description**: Displays conversation memory/history
- **Functionality**: Shows role, content preview, and timestamp for each conversation turn

### Tools Display Tool
- **Name**: `show_tools`
- **Description**: Lists all available tools and their descriptions
- **Functionality**: Provides overview of agent capabilities

## Technical Details

### Email Connection (IMAP)
- **Server**: imap.gmx.net
- **Port**: 993 (SSL/TLS)
- **Protocol**: IMAP4_SSL
- **Account**: alois_wirth@gmx.de
- **Authentication**: Password from GMX_PW environment variable

### Calendar Connection (CalDAV)
- **Server**: caldav.gmx.net
- **URL**: https://caldav.gmx.net/begenda/dav/{email}/calendar/
- **Protocol**: CalDAV over HTTPS
- **Account**: alois_wirth@gmx.de
- **Authentication**: App-specific password from GMX_KALENDER environment variable
- **Fallback**: Local storage if CalDAV fails
- **Known Issue**: GMX CalDAV returns 403 Forbidden on event creation despite successful authentication and correct URL format
- **Note**: URL format matches Thunderbird configuration

### Email Processing
- Handles multipart MIME messages with improved extraction
- Decodes email headers (subject, from, date)
- Extracts plain text body content (text/plain preferred)
- Falls back to HTML content with tag stripping if no plain text available
- Skips email attachments automatically
- Handles various character encodings (UTF-8, ISO-8859-1, etc.)
- Handles encoding issues gracefully with error replacement
- Truncates long emails to 500 characters for display

### Error Handling
- Catches connection errors (IMAP and CalDAV)
- Handles authentication failures
- Manages email decoding issues
- Gracefully falls back to local storage if CalDAV fails
- Provides user-friendly error messages
- Records failures in decision log
- Skips read-only calendars automatically

## Inputs/Outputs

### Inputs
- User text prompts via Marimo UI
- Environment variables (API keys, passwords)
- GMX email account credentials

### Outputs
- Formatted email content
- Calendar event confirmations
- Decision logs
- Conversation history
- Tool descriptions
- Error messages (if any)

### Side Effects
- Connects to GMX IMAP server
- Reads emails from remote server
- Connects to GMX CalDAV server (if available)
- Creates calendar events in GMX calendar
- Updates agent_state dictionary
- Records decisions and memory history

## Assumptions & Limits

### Assumptions
- Valid GMX account credentials in .env file
- Active internet connection
- OpenAI API key is valid and has credits
- GMX IMAP server is accessible
- GMX CalDAV server is accessible (optional, falls back to local)
- Email content is primarily text-based
- User has at least one writable calendar in GMX account

### Limits
- Email body truncated to 500 characters for display
- Default reads last 10 emails (configurable)
- Calendar events may fall back to local storage if CalDAV fails
- Calendar events default to 1-hour duration
- Requires SSL/TLS connection to GMX
- No support for sending emails (read-only)
- No support for email attachments
- HTML emails converted to plain text or skipped
- CalDAV may have authorization issues (GMX-specific)

## Version/Change Log

### Version 3.3 (Current)
- **Fixed**: Corrected CalDAV URL to include /calendar/ path (matches Thunderbird config)
- **Changed**: URL now: https://caldav.gmx.net/begenda/dav/{email}/calendar/
- **Improved**: Direct calendar access (no birthday calendar in list)
- **Issue**: GMX CalDAV still returns 403 Forbidden on event creation (GMX server-side limitation)

### Version 3.2
- **Changed**: CalDAV now uses app-specific password (GMX_KALENDER) instead of main password
- **Added**: Separate authentication for calendar operations
- **Changed**: Updated .env.example with GMX_KALENDER configuration
- **Issue**: GMX CalDAV still returns 403 Forbidden on event creation (GMX limitation)

### Version 3.1
- **Fixed**: Improved email body extraction for multipart messages
- **Added**: HTML email support with tag stripping fallback
- **Added**: Better handling of various character encodings
- **Added**: Automatic attachment skipping
- **Changed**: Enhanced multipart message parsing
- **Issue**: Fixed issue where some email bodies were not being read

### Version 3.0
- **Added**: GMX CalDAV calendar integration
- **Added**: Real calendar event creation in GMX calendar
- **Added**: Fallback to local storage if CalDAV fails
- **Added**: Flexible date/time parsing with dateutil
- **Added**: Timezone support (Europe/Berlin)
- **Added**: Automatic skipping of read-only calendars
- **Changed**: Calendar tool now attempts GMX sync first
- **Changed**: Enhanced error handling for CalDAV operations
- **Issue**: N/A (Feature enhancement)

### Version 2.0
- **Changed**: Replaced fake email with real GMX IMAP integration
- **Added**: GMX email configuration (server, port, credentials)
- **Added**: IMAP connection and authentication
- **Added**: Email decoding and formatting
- **Added**: Error handling for email operations
- **Changed**: Updated tool description to reflect real email reading
- **Changed**: Modified EmailReadInput to accept count parameter
- **Changed**: Updated system prompt to mention GMX account
- **Issue**: N/A (Feature enhancement)

### Version 1.0
- Initial version with fake email content
- Basic LangChain agent setup
- Calendar event creation
- Memory and decision tracking tools

## Test Links
- Test file: `test/test_agent_demo.py`
- Coverage report: `htmlcov/index.html` (after running pytest with coverage)

## Owner
Maintainer: Alois Wirth
Email: alois_wirth@gmx.de

## Security Notes
- GMX passwords stored in .env file (not committed to git)
- Uses separate app-specific password for calendar access (GMX_KALENDER)
- .env file should be in .gitignore
- OpenAI API key should be kept secure
- IMAP connection uses SSL/TLS encryption
- CalDAV connection uses HTTPS
- Credentials never logged or displayed in output

## Dependencies
- marimo: Interactive notebook framework
- langchain: Agent framework
- langchain-openai: OpenAI integration
- python-dotenv: Environment variable management
- imaplib: Built-in Python IMAP client
- email: Built-in Python email parsing
- caldav: CalDAV client for calendar integration
- icalendar: iCalendar format handling
- pytz: Timezone support
- python-dateutil: Flexible date/time parsing
- pydantic: Data validation

## Future Enhancements
- Add email filtering by sender/subject
- Support for reading specific folders
- Email search functionality
- Attachment handling
- HTML email rendering
- Email sending capability
- Resolve GMX CalDAV authorization issues
- Support for app-specific passwords
- Custom event duration
- Recurring events support
- Calendar event editing/deletion
- Export calendar to .ics format
- Multiple calendar support
