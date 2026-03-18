#!/usr/bin/env python3
"""
Script to set up Gmail push notifications with webhook endpoint
Run this after deploying to Render to configure Gmail to push to your webhook
"""

import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def setup_gmail_webhook(webhook_url):
    """Set up Gmail push notifications to webhook endpoint"""
    
    # Get credentials
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('gmail', 'v1', credentials=creds)
    
    # Set up watch request
    request = {
        'labelIds': ['INBOX'],
        'topicName': f'projects/{os.getenv("GOOGLE_PROJECT_ID")}/topics/gmail-notifications'
    }
    
    try:
        # Start watching
        result = service.users().watch(userId='me', body=request).execute()
        print(f"✅ Gmail watch activated successfully!")
        print(f"History ID: {result.get('historyId')}")
        print(f"Expiration: {result.get('expiration')}")
        
        print(f"\n📋 Next steps:")
        print(f"1. Your webhook URL: {webhook_url}")
        print(f"2. Gmail will push notifications to: {webhook_url}/webhook/gmail")
        print(f"3. Make sure your Pub/Sub topic pushes to this webhook URL")
        
        return result
        
    except Exception as e:
        print(f"❌ Error setting up Gmail watch: {e}")
        return None

def configure_pubsub_push(webhook_url, subscription_name):
    """Configure Pub/Sub subscription to push to webhook"""
    
    print(f"\n🔧 To configure Pub/Sub push subscription:")
    print(f"Run this command in Google Cloud Shell:")
    print(f"""
gcloud pubsub subscriptions modify {subscription_name} \\
    --push-endpoint={webhook_url}/webhook/gmail \\
    --project={os.getenv('GOOGLE_PROJECT_ID')}
    """)

if __name__ == '__main__':
    # Get webhook URL from user
    webhook_url = input("Enter your Render app URL (e.g., https://your-app.onrender.com): ").strip()
    
    if not webhook_url:
        print("❌ Please provide a valid webhook URL")
        exit(1)
    
    if not webhook_url.startswith('http'):
        webhook_url = f"https://{webhook_url}"
    
    print(f"🚀 Setting up Gmail webhook for: {webhook_url}")
    
    # Setup Gmail watch
    result = setup_gmail_webhook(webhook_url)
    
    if result:
        # Show Pub/Sub configuration
        configure_pubsub_push(webhook_url, "gmail-notifications-sub")
        
        print(f"\n✅ Setup complete!")
        print(f"Your Gmail Agent is now ready to receive push notifications!")
    else:
        print(f"❌ Setup failed. Please check your credentials and try again.")