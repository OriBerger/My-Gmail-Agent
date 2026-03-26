import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.pubsub_v1 import SubscriberClient
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/pubsub'
]

PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID')
SUBSCRIPTION_ID = "gmail-notifications-sub"

def get_credentials():
    """Get authenticated credentials for Google APIs"""
    creds = None
    # Load existing token if available
    if os.path.exists('token.json'):
        print("Loading existing token...")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("Getting new credentials...")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    print("Credentials obtained successfully!")
    return creds

def test_pubsub():
    print("Testing Pub/Sub connection...")
    creds = get_credentials()
    subscriber = SubscriberClient(credentials=creds)
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    print(f"Subscription path: {subscription_path}")
    
    # Try to pull messages (should work even if no messages)
    try:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 1}
        )
        print("SUCCESS: Pub/Sub connection successful!")
        print(f"Messages received: {len(response.received_messages)}")
        return True
    except Exception as e:
        print(f"ERROR: Pub/Sub error: {e}")
        return False

if __name__ == '__main__':
    print("Testing Gmail Agent authentication...")
    success = test_pubsub()
    if success:
        print("SUCCESS: All tests passed! Your agent should work now.")
    else:
        print("FAILED: Tests failed. Check your Google Cloud setup.")