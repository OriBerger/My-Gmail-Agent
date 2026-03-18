#!/usr/bin/env python3
"""
Show the correct Pub/Sub commands for your deployment
"""

import os
from dotenv import load_dotenv

load_dotenv()

def show_commands():
    """Show the correct gcloud commands"""
    
    project_id = os.getenv('GOOGLE_PROJECT_ID', 'project-adccce59-2a50-4dce-87f')
    webhook_url = "https://my-gmail-agent.onrender.com"  # Your actual URL
    
    print("CORRECT GOOGLE CLOUD COMMANDS")
    print("=" * 50)
    print()
    print("Copy and paste these commands in Google Cloud Shell:")
    print()
    print("# 1. Delete existing subscription")
    print(f"gcloud pubsub subscriptions delete gmail-notifications-sub \\")
    print(f"    --project={project_id}")
    print()
    print("# 2. Create new push subscription")
    print(f"gcloud pubsub subscriptions create gmail-notifications-sub \\")
    print(f"    --topic=gmail-notifications \\")
    print(f"    --push-endpoint={webhook_url}/webhook/gmail \\")
    print(f"    --project={project_id}")
    print()
    print("# 3. Verify the subscription")
    print(f"gcloud pubsub subscriptions describe gmail-notifications-sub \\")
    print(f"    --project={project_id}")
    print()
    print("# 4. Test the webhook")
    print(f"curl -X POST {webhook_url}/webhook/gmail \\")
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"message":{"data":"eyJ0ZXN0IjoidGVzdCJ9","messageId":"test123"}}\'')
    print()
    print("Expected response: {\"status\": \"success\", \"message\": \"Webhook received\"}")

if __name__ == '__main__':
    show_commands()