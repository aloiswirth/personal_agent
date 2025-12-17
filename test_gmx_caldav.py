#!/usr/bin/env python3
"""Test script to verify GMX CalDAV connection"""

import os
from dotenv import load_dotenv
import caldav
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz

# Load environment variables
load_dotenv()

GMX_EMAIL = "alois_wirth@gmx.de"
GMX_CALDAV_PASSWORD = os.getenv("GMX_KALENDER")  # App-specific password for calendar
# Try different GMX CalDAV URLs (including /calendar path as per Thunderbird config)
GMX_CALDAV_URLS = [
    f"https://caldav.gmx.net/begenda/dav/{GMX_EMAIL}/calendar/",
    "https://caldav.gmx.net/begenda/dav/",
    f"https://caldav.gmx.net/begenda/dav/{GMX_EMAIL}/",
    "https://caldav.gmx.net/",
]

print("🔍 Testing GMX CalDAV Connection...")
print(f"Email: {GMX_EMAIL}")
print()

client = None
working_url = None

# Try different URLs
for url in GMX_CALDAV_URLS:
    try:
        print(f"📡 Trying CalDAV URL: {url}")
        client = caldav.DAVClient(
            url=url,
            username=GMX_EMAIL,
            password=GMX_CALDAV_PASSWORD
        )
        # Test if we can get principal
        principal = client.principal()
        working_url = url
        print(f"✅ Connection successful with URL: {url}")
        break
    except Exception as e:
        print(f"❌ Failed with {url}: {str(e)[:100]}")
        continue

if client and working_url:
    print(f"\n✅ Using working URL: {working_url}")
    
    # Principal already retrieved during URL testing
    print("👤 Principal confirmed")
    
    # Get calendars
    print("📅 Fetching calendars...")
    calendars = principal.calendars()
    print(f"✅ Found {len(calendars)} calendar(s)")
    
    for i, cal in enumerate(calendars, 1):
        print(f"   {i}. {cal.name if hasattr(cal, 'name') else 'Calendar ' + str(i)}")
    
    if calendars:
        # Find a writable calendar (skip birthday calendars which are read-only)
        calendar = None
        for cal in calendars:
            cal_name = cal.name if hasattr(cal, 'name') else 'Unknown'
            # Skip birthday/read-only calendars
            if 'geburtstag' not in cal_name.lower() and 'birthday' not in cal_name.lower():
                calendar = cal
                print(f"\n📝 Using calendar: {cal_name}")
                break
        
        if not calendar:
            # If no suitable calendar found, use the last one
            calendar = calendars[-1]
            print(f"\n📝 Using calendar: {calendar.name if hasattr(calendar, 'name') else 'Default Calendar'}")
        
        # Create a test event
        print("\n🧪 Creating test event...")
        
        # Create iCalendar event with all required fields
        cal = Calendar()
        
        # Add required calendar properties
        cal.add('prodid', '-//LangChain Agent Demo//CalDAV Client//EN')
        cal.add('version', '2.0')
        
        event = Event()
        
        # Generate unique UID
        import uuid
        event.add('uid', str(uuid.uuid4()))
        
        # Set event properties
        event.add('summary', 'Test Event from Agent Demo')
        event.add('description', 'This is a test event created by the LangChain agent demo')
        
        # Set start and end times (1 hour from now, duration 1 hour)
        start_time = datetime.now(pytz.UTC) + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        event.add('dtstart', start_time)
        event.add('dtend', end_time)
        event.add('dtstamp', datetime.now(pytz.UTC))  # Required: timestamp of creation
        event.add('location', 'Test Location')
        
        # Add event to calendar
        cal.add_component(event)
        
        # Save to CalDAV server
        try:
            calendar.save_event(cal.to_ical())
            print("✅ Test event created successfully!")
        except Exception as save_error:
            print(f"❌ Error saving event: {save_error}")
            print("\n📋 Detailed Error Information:")
            print(f"Error Type: {type(save_error).__name__}")
            print(f"Error Message: {str(save_error)}")
            
            # Try to get more details from the caldav client
            if hasattr(save_error, '__dict__'):
                print("\nError Attributes:")
                for key, value in save_error.__dict__.items():
                    print(f"  {key}: {value}")
            
            # Try to make a direct PUT request to see the full response
            print("\n🔍 Attempting direct PUT request to capture full response...")
            try:
                import requests
                from requests.auth import HTTPBasicAuth
                
                # Generate a unique event ID
                import uuid
                event_id = str(uuid.uuid4())
                event_url = f"{working_url}{event_id}.ics"
                
                print(f"PUT URL: {event_url}")
                print(f"Username: {GMX_EMAIL}")
                print(f"Using app-specific password: {'*' * len(GMX_CALDAV_PASSWORD) if GMX_CALDAV_PASSWORD else 'None'}")
                
                headers = {
                    'Content-Type': 'text/calendar; charset=utf-8',
                    'User-Agent': 'CalDAV-Test/1.0'
                }
                
                response = requests.put(
                    event_url,
                    data=cal.to_ical(),
                    auth=HTTPBasicAuth(GMX_EMAIL, GMX_CALDAV_PASSWORD),
                    headers=headers
                )
                
                print(f"\n📡 HTTP Response:")
                print(f"Status Code: {response.status_code}")
                print(f"Reason: {response.reason}")
                print(f"\n📋 Response Headers:")
                for header, value in response.headers.items():
                    print(f"  {header}: {value}")
                print(f"\n📄 Response Body:")
                print(response.text)
                
            except Exception as req_error:
                print(f"❌ Direct request also failed: {req_error}")
            
            raise
        
        print()
        print("🎉 SUCCESS! GMX CalDAV connection is working correctly.")
        print("📅 You can now create calendar events in your GMX calendar.")
        print("\n⚠️  Note: A test event was created. You may want to delete it from your calendar.")
    else:
        print("\n⚠️  No calendars found. Please create a calendar in your GMX account first.")
    
else:
    print("\n❌ Could not connect to GMX CalDAV server with any known URL")
    print("\nTroubleshooting:")
    print("1. Check your GMX credentials in the .env file")
    print("2. Verify your internet connection")
    print("3. Ensure CalDAV access is enabled in your GMX account")
    print("4. Contact GMX support for the correct CalDAV URL")
