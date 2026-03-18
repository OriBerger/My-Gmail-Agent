import os
import json
import base64
import logging
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/pubsub'
]

PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-secret-key')

def get_credentials():
    """Get authenticated credentials for Google APIs"""
    creds = None
    
    # For production, use service account or other auth method
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # In production, this should be handled differently
            logger.warning("No valid credentials found. Manual authentication required.")
            return None
        
        # Save credentials for next run
        try:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        except (PermissionError, OSError) as e:
            logger.warning(f"Could not save token.json: {e}. Credentials will not persist.")
            # Continue without saving - credentials will work for this session
    
    return creds

def get_gmail_service():
    """Get Gmail service client"""
    creds = get_credentials()
    if not creds:
        return None
    return build('gmail', 'v1', credentials=creds)

def fetch_email_content(service, message_id):
    """Fetch email content by message ID"""
    try:
        msg = service.users().messages().get(userId='me', id=message_id).execute()
        
        # Extract email content safely
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        
        # Get subject and sender
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        
        # Get body with comprehensive safety checks
        body = ""
        parts = payload.get('parts', [])
        
        if parts:
            # Multi-part email (has parts)
            for part in parts:
                mime_type = part.get('mimeType', '')
                if mime_type == 'text/plain':
                    part_body = part.get('body', {})
                    data = part_body.get('data', '')
                    if data:
                        try:
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                            break
                        except Exception as decode_error:
                            logger.warning(f"Failed to decode email part: {decode_error}")
                            continue
        else:
            # Single-part email (no parts)
            mime_type = payload.get('mimeType', '')
            if mime_type == 'text/plain':
                payload_body = payload.get('body', {})
                data = payload_body.get('data', '')
                if data:
                    try:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                    except Exception as decode_error:
                        logger.warning(f"Failed to decode email body: {decode_error}")
                        body = "Could not decode email content"
        
        return f"From: {sender}\nSubject: {subject}\n\n{body}"
    
    except Exception as e:
        logger.error(f"Error fetching email content: {e}")
        return f"Error fetching email: {str(e)}"

def process_and_send(content):
    """Process email content and send summary via WhatsApp"""
    try:
        # Initialize clients
        llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
        twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        
        # Create summary
        prompt = ChatPromptTemplate.from_template(
            "You are a personal assistant. Summarize the following email in one short, concise sentence in Hebrew. "
            "If it's unimportant advertising, just write 'Unimportant advertisement'.\n\n{content}"
        )
        chain = prompt | llm
        summary = chain.invoke({"content": content}).content
        
        # Send WhatsApp message
        twilio_client.messages.create(
            from_=os.getenv('TWILIO_WHATSAPP_NUMBER'),
            body=f"*Gmail Summary:*\n{summary}",
            to=os.getenv('MY_NUMBER')
        )
        
        logger.info(f"Summary sent: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Error processing email: {e}")
        return None

@app.route('/')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Gmail Agent',
        'version': '1.0.0'
    })

@app.route('/webhook/gmail', methods=['POST'])
def gmail_webhook():
    """Handle Gmail push notifications"""
    try:
        # Verify webhook (optional but recommended)
        # auth_header = request.headers.get('Authorization')
        # if not auth_header or auth_header != f"Bearer {WEBHOOK_SECRET}":
        #     return jsonify({'error': 'Unauthorized'}), 401
        
        # Parse the notification
        data = request.get_json()
        logger.info(f"Received webhook: {data}")
        
        # Extract message from Pub/Sub format
        if 'message' in data:
            message_data = data['message']
            if 'data' in message_data:
                # Decode the base64 data
                decoded_data = base64.b64decode(message_data['data']).decode('utf-8')
                notification = json.loads(decoded_data)
                
                email_address = notification.get('emailAddress')
                history_id = notification.get('historyId')
                
                logger.info(f"New email notification from: {email_address}")
                
                # Get Gmail service
                service = get_gmail_service()
                if not service:
                    return jsonify({'error': 'Gmail service not available'}), 500
                
                # Get the latest unread message
                results = service.users().messages().list(
                    userId='me', 
                    q="is:unread", 
                    maxResults=1
                ).execute()
                
                messages = results.get('messages', [])
                
                if messages:
                    # Process the email
                    content = fetch_email_content(service, messages[0]['id'])
                    summary = process_and_send(content)
                    
                    if summary:
                        # Mark as read
                        service.users().messages().batchModify(
                            userId='me',
                            body={
                                'ids': [messages[0]['id']], 
                                'removeLabelIds': ['UNREAD']
                            }
                        ).execute()
                        
                        return jsonify({
                            'status': 'success',
                            'message': 'Email processed successfully',
                            'summary': summary
                        })
                    else:
                        return jsonify({'error': 'Failed to process email'}), 500
                else:
                    return jsonify({
                        'status': 'no_messages',
                        'message': 'No unread messages found'
                    })
        
        return jsonify({'status': 'success', 'message': 'Webhook received'})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/test', methods=['POST'])
def test_endpoint():
    """Test endpoint for development"""
    try:
        service = get_gmail_service()
        if not service:
            return jsonify({'error': 'Gmail service not available'}), 500
        
        # Get the latest email
        results = service.users().messages().list(userId='me', maxResults=1).execute()
        messages = results.get('messages', [])
        
        if messages:
            content = fetch_email_content(service, messages[0]['id'])
            summary = process_and_send(content)
            
            return jsonify({
                'status': 'success',
                'content': content[:200] + '...',  # Truncate for response
                'summary': summary
            })
        else:
            return jsonify({'message': 'No messages found'})
            
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)