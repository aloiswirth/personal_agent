#!/usr/bin/env python3
"""Test script to diagnose email body reading issues"""

import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GMX_EMAIL = "alois_wirth@gmx.de"
GMX_PASSWORD = os.getenv("GMX_PW")
GMX_IMAP_SERVER = "imap.gmx.net"
GMX_IMAP_PORT = 993

print("🔍 Testing Email Body Reading...")
print(f"Email: {GMX_EMAIL}")
print()

try:
    # Connect to GMX IMAP server
    mail = imaplib.IMAP4_SSL(GMX_IMAP_SERVER, GMX_IMAP_PORT)
    mail.login(GMX_EMAIL, GMX_PASSWORD)
    mail.select("INBOX")

    # Get last 3 emails for testing
    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    email_ids = email_ids[-3:]  # Last 3 emails
    
    print(f"Testing last {len(email_ids)} emails\n")
    print("=" * 80)
    
    for i, email_id in enumerate(reversed(email_ids), 1):
        print(f"\n📧 Email {i}:")
        print("-" * 80)
        
        # Fetch the email
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                # Get subject
                subject = msg["Subject"]
                if subject:
                    decoded_subject = decode_header(subject)[0]
                    if isinstance(decoded_subject[0], bytes):
                        subject = decoded_subject[0].decode(decoded_subject[1] or "utf-8")
                    else:
                        subject = decoded_subject[0]
                
                print(f"Subject: {subject}")
                print(f"From: {msg.get('From', 'Unknown')}")
                print(f"Date: {msg.get('Date', 'Unknown')}")
                print(f"Content-Type: {msg.get_content_type()}")
                print(f"Is multipart: {msg.is_multipart()}")
                print()
                
                # Try different methods to extract body
                body = ""
                body_found = False
                
                if msg.is_multipart():
                    print("📦 Multipart message - checking all parts:")
                    for part_num, part in enumerate(msg.walk(), 1):
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition", ""))
                        
                        print(f"  Part {part_num}: {content_type}, Disposition: {content_disposition}")
                        
                        # Skip attachments
                        if "attachment" in content_disposition:
                            print(f"    → Skipping attachment")
                            continue
                        
                        # Try to get text/plain first
                        if content_type == "text/plain" and not body_found:
                            try:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    charset = part.get_content_charset() or 'utf-8'
                                    body = payload.decode(charset, errors='replace')
                                    body_found = True
                                    print(f"    ✅ Found text/plain body ({len(body)} chars)")
                            except Exception as e:
                                print(f"    ❌ Error decoding text/plain: {e}")
                        
                        # If no text/plain, try text/html
                        elif content_type == "text/html" and not body_found:
                            try:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    charset = part.get_content_charset() or 'utf-8'
                                    html_body = payload.decode(charset, errors='replace')
                                    # Simple HTML stripping (for testing)
                                    import re
                                    body = re.sub('<[^<]+?>', '', html_body)
                                    body_found = True
                                    print(f"    ✅ Found text/html body ({len(body)} chars, stripped HTML)")
                            except Exception as e:
                                print(f"    ❌ Error decoding text/html: {e}")
                else:
                    print("📄 Single-part message:")
                    content_type = msg.get_content_type()
                    print(f"  Content-Type: {content_type}")
                    
                    try:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            charset = msg.get_content_charset() or 'utf-8'
                            body = payload.decode(charset, errors='replace')
                            body_found = True
                            print(f"  ✅ Decoded body ({len(body)} chars)")
                    except Exception as e:
                        print(f"  ❌ Error decoding: {e}")
                        # Try without decoding
                        try:
                            body = str(msg.get_payload())
                            body_found = True
                            print(f"  ⚠️ Got body without decoding ({len(body)} chars)")
                        except Exception as e2:
                            print(f"  ❌ Error getting payload: {e2}")
                
                print()
                if body_found and body:
                    print("📝 Body preview (first 300 chars):")
                    print(body[:300])
                    if len(body) > 300:
                        print(f"... ({len(body) - 300} more characters)")
                else:
                    print("⚠️ No body content found!")
                
                print("\n" + "=" * 80)
    
    mail.close()
    mail.logout()
    
    print("\n✅ Test complete!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
