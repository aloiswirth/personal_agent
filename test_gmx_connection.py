#!/usr/bin/env python3
"""Test script to verify GMX email connection"""

import os
import imaplib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GMX_EMAIL = "alois_wirth@gmx.de"
GMX_PASSWORD = os.getenv("GMX_PW")
GMX_IMAP_SERVER = "imap.gmx.net"
GMX_IMAP_PORT = 993

print("🔍 Testing GMX IMAP Connection...")
print(f"Email: {GMX_EMAIL}")
print(f"Server: {GMX_IMAP_SERVER}:{GMX_IMAP_PORT}")
print()

try:
    # Connect to GMX IMAP server
    print("📡 Connecting to GMX IMAP server...")
    mail = imaplib.IMAP4_SSL(GMX_IMAP_SERVER, GMX_IMAP_PORT)
    print("✅ Connection established")
    
    # Login
    print(f"🔐 Authenticating as {GMX_EMAIL}...")
    mail.login(GMX_EMAIL, GMX_PASSWORD)
    print("✅ Authentication successful")
    
    # Select inbox
    print("📬 Selecting INBOX...")
    mail.select("INBOX")
    print("✅ INBOX selected")
    
    # Search for all emails
    print("🔍 Searching for emails...")
    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    print(f"✅ Found {len(email_ids)} emails in INBOX")
    
    # Close connection
    mail.close()
    mail.logout()
    print("✅ Connection closed")
    
    print()
    print("🎉 SUCCESS! GMX email connection is working correctly.")
    print(f"📧 You have {len(email_ids)} emails in your inbox.")
    
except imaplib.IMAP4.error as e:
    print(f"❌ IMAP Error: {e}")
    print("Please check your credentials in the .env file")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Please check your internet connection and credentials")
