import os
import base64
import json
from google.pubsub_v1 import SubscriberClient
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# הגדרות
PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID')
SUBSCRIPTION_ID = "gmail-notifications-sub"
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/pubsub'
]

# אתחול AI וטוויליו
# llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
# twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

def get_credentials():
    """Get authenticated credentials for Google APIs"""
    creds = None
    # Load existing token if available
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def get_gmail_service():
    creds = get_credentials()
    return build('gmail', 'v1', credentials=creds)

def fetch_email_content(service, message_id):
    """מושכת את תוכן המייל לפי ה-ID שקיבלנו מההתראה"""
    msg = service.users().messages().get(userId='me', id=message_id).execute()
    payload = msg.get('payload', {})
    headers = payload.get('headers', [])
    subject = next(h['value'] for h in headers if h['name'] == 'Subject')
    
    # חילוץ גוף המייל (פשוט)
    parts = payload.get('parts', [])
    if not parts:
        data = payload.get('body', {}).get('data', '')
    else:
        data = parts[0].get('body', {}).get('data', '')
    
    if data:
        body = base64.urlsafe_b64decode(data).decode('utf-8')
        return f"נושא: {subject}\nתוכן: {body}"
    return f"נושא: {subject} (ללא תוכן טקסטואלי)"

def process_and_send(content):
    """מתמצת ושולח לוואטסאפ"""
    # Initialize clients locally to avoid hanging on startup
    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
    twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
    
    prompt = ChatPromptTemplate.from_template(
        "אתה עוזר אישי. תמצת את המייל הבא למשפט אחד קצר וענייני בעברית. "
        "אם מדובר בפרסומת לא חשובה, כתוב רק 'פרסומת לא מעניינת'.\n\n{content}"
    )
    chain = prompt | llm
    summary = chain.invoke({"content": content}).content
    
    twilio_client.messages.create(
        from_=os.getenv('TWILIO_WHATSAPP_NUMBER'),
        body=f"*Gmail Summary:*\n{summary}",
        to=os.getenv('MY_NUMBER')
    )
    print(f"Summary sent: {summary}")

def callback(received_message):
    """פונקציה שרצה בכל פעם שמתקבלת הודעה ב-Pub/Sub"""
    try:
        data = json.loads(received_message.message.data.decode('utf-8'))
        email_address = data.get('emailAddress')
        print(f"New email received from: {email_address}")
        
        service = get_gmail_service()
        # מושכים את המייל האחרון שלא נקרא
        results = service.users().messages().list(userId='me', q="is:unread", maxResults=1).execute()
        messages = results.get('messages', [])
        
        if messages:
            content = fetch_email_content(service, messages[0]['id'])
            process_and_send(content)
            # סימון כנקרא כדי שלא יתעבד שוב
            service.users().messages().batchModify(
                userId='me', 
                body={'ids': [messages[0]['id']], 'removeLabelIds': ['UNREAD']}
            ).execute()
            
    except Exception as e:
        print(f"Error processing message: {e}")

# הפעלת המאזין
def main():
    # שימוש באותן הרשאות של Gmail גם עבור Pub/Sub
    creds = get_credentials()
    subscriber = SubscriberClient(credentials=creds)
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    print(f"System is running! Listening for emails on subscription: {SUBSCRIPTION_ID}...")

    # Pull messages continuously
    try:
        while True:
            response = subscriber.pull(
                request={"subscription": subscription_path, "max_messages": 10}
            )
            
            if response.received_messages:
                for received_message in response.received_messages:
                    callback(received_message)
                    # Acknowledge the message
                    subscriber.acknowledge(
                        request={"subscription": subscription_path, "ack_ids": [received_message.ack_id]}
                    )
            
            import time
            time.sleep(1)  # Wait 1 second before next pull
            
    except KeyboardInterrupt:
        print("Stopping Gmail agent...")

if __name__ == '__main__':
    main()