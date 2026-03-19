import os
import json
import base64
import logging
import warnings
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from twilio.rest import Client
from dotenv import load_dotenv

# Suppress Google API cache warnings
warnings.filterwarnings("ignore", message="file_cache is only supported with oauth2client<4.0.0")
warnings.filterwarnings("ignore", module="googleapiclient.discovery_cache")

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

# Circuit breaker for failed email processing
failed_attempts = {}
MAX_FAILED_ATTEMPTS = 3
FAILURE_RESET_TIME = 300  # 5 minutes in seconds

# Processed messages tracking to prevent duplicate processing
processed_messages = set()
PROCESSED_MESSAGES_MAX_SIZE = 1000  # Limit memory usage

def should_skip_processing(message_id):
    """Check if we should skip processing this message due to too many failures"""
    import time
    
    if message_id not in failed_attempts:
        return False
    
    failure_info = failed_attempts[message_id]
    current_time = time.time()
    
    # Reset counter if enough time has passed
    if current_time - failure_info['last_attempt'] > FAILURE_RESET_TIME:
        del failed_attempts[message_id]
        return False
    
    # Skip if we've exceeded max attempts
    if failure_info['count'] >= MAX_FAILED_ATTEMPTS:
        logger.warning(f"Skipping message {message_id} - exceeded {MAX_FAILED_ATTEMPTS} failed attempts")
        return True
    
    return False

def record_failure(message_id):
    """Record a failed processing attempt"""
    import time
    
    current_time = time.time()
    
    if message_id not in failed_attempts:
        failed_attempts[message_id] = {'count': 0, 'last_attempt': current_time}
    
    failed_attempts[message_id]['count'] += 1
    failed_attempts[message_id]['last_attempt'] = current_time
    
    logger.warning(f"Recording failure for message {message_id} - attempt {failed_attempts[message_id]['count']}/{MAX_FAILED_ATTEMPTS}")

def record_success(message_id):
    """Record a successful processing attempt"""
    if message_id in failed_attempts:
        del failed_attempts[message_id]
        logger.info(f"Cleared failure record for message {message_id} after successful processing")

def is_message_already_processed(message_id):
    """Check if message was already processed"""
    return message_id in processed_messages

def mark_message_as_processed(message_id):
    """Mark message as processed and manage memory usage"""
    global processed_messages
    
    # If we're approaching memory limit, clear old entries
    if len(processed_messages) >= PROCESSED_MESSAGES_MAX_SIZE:
        # Keep only the most recent half
        processed_messages = set(list(processed_messages)[PROCESSED_MESSAGES_MAX_SIZE//2:])
        logger.info(f"Cleared old processed message records, keeping {len(processed_messages)} recent ones")
    
    processed_messages.add(message_id)
    logger.info(f"Marked message {message_id} as processed")

def get_credentials():
    """Get authenticated credentials for Google APIs"""
    creds = None
    
    # Check for token in environment variable first (for Render deployment)
    gmail_token_json = os.getenv('GMAIL_TOKEN_JSON')
    if gmail_token_json and not os.path.exists('token.json'):
        try:
            # Create temporary token file from environment variable only if it doesn't exist
            with open('token.json', 'w') as f:
                f.write(gmail_token_json)
            logger.info("Created token.json from environment variable")
        except Exception as e:
            logger.error(f"Failed to create token.json from env var: {e}")
    elif gmail_token_json and os.path.exists('token.json'):
        logger.debug("token.json already exists, skipping creation from environment variable")
    
    # Load credentials from token file
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
        llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
        twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        
        # Create summary
        prompt = ChatPromptTemplate.from_template(
            "You are a personal Gmail assistant. Summarize the following email in one or two short, concise sentences in Hebrew, no need for titles or anything like that, just provide the sentences.\n\n{content}"
        )
        chain = prompt | llm
        summary = chain.invoke({"content": content}).content
        
        # Send WhatsApp message
        twilio_client.messages.create(
            from_=os.getenv('TWILIO_WHATSAPP_NUMBER'),
            body=f"*New email summary:*\n{summary}",
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
        
        # Get the Pub/Sub message ID for deduplication
        pubsub_message_id = None
        if 'message' in data and 'messageId' in data['message']:
            pubsub_message_id = data['message']['messageId']
            
            # Check if we already processed this Pub/Sub message (prevent duplicate webhook processing)
            if is_message_already_processed(f"pubsub_{pubsub_message_id}"):
                logger.info(f"Pub/Sub message {pubsub_message_id} already processed, skipping duplicate webhook")
                return jsonify({
                    'status': 'already_processed',
                    'message': f'Pub/Sub message {pubsub_message_id} was already processed'
                }), 200
            
            # Mark this Pub/Sub message as processed immediately to prevent race conditions
            mark_message_as_processed(f"pubsub_{pubsub_message_id}")
        
        # Extract message from Pub/Sub format
        if 'message' in data:
            message_data = data['message']
            if 'data' in message_data:
                # Decode the base64 data
                decoded_data = base64.b64decode(message_data['data']).decode('utf-8')
                notification = json.loads(decoded_data)
                
                email_address = notification.get('emailAddress')
                history_id = notification.get('historyId')
                
                logger.info(f"New email notification from: {email_address}, historyId: {history_id}")
                
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
                    message_id = messages[0]['id']
                    
                    # Check if we already processed this Gmail message (prevent duplicate processing)
                    if is_message_already_processed(message_id):
                        logger.info(f"Gmail message {message_id} already processed, skipping duplicate")
                        return jsonify({
                            'status': 'already_processed',
                            'message': f'Gmail message {message_id} was already processed'
                        }), 200
                    
                    # Mark this Gmail message as processed immediately to prevent race conditions
                    mark_message_as_processed(message_id)
                    
                    # Check if we should skip this message due to previous failures
                    if should_skip_processing(message_id):
                        return jsonify({
                            'status': 'skipped',
                            'message': f'Message {message_id} skipped due to repeated failures'
                        }), 200
                    
                    try:
                        # Process the email
                        content = fetch_email_content(service, message_id)
                        summary = process_and_send(content)
                        
                        if summary:
                            # Mark as read
                            service.users().messages().batchModify(
                                userId='me',
                                body={
                                    'ids': [message_id], 
                                    'removeLabelIds': ['UNREAD']
                                }
                            ).execute()
                            
                            # Record success (clears any previous failures)
                            record_success(message_id)
                            
                            return jsonify({
                                'status': 'success',
                                'message': 'Email processed successfully',
                                'summary': summary
                            }), 200
                        else:
                            # Record failure
                            record_failure(message_id)
                            return jsonify({'error': 'Failed to process email'}), 500
                    
                    except Exception as e:
                        # Record failure for any exception during processing
                        record_failure(message_id)
                        logger.error(f"Error processing message {message_id}: {e}")
                        return jsonify({'error': f'Processing failed: {str(e)}'}), 500
                else:
                    return jsonify({
                        'status': 'no_messages',
                        'message': 'No unread messages found'
                    }), 200
        
        return jsonify({'status': 'success', 'message': 'Webhook received'}), 200
        
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

@app.route('/circuit-breaker', methods=['GET'])
def circuit_breaker_status():
    """Get circuit breaker status"""
    import time
    current_time = time.time()
    
    status = {}
    for message_id, failure_info in failed_attempts.items():
        time_since_last = current_time - failure_info['last_attempt']
        status[message_id] = {
            'failed_attempts': failure_info['count'],
            'last_attempt_ago': f"{int(time_since_last)}s",
            'will_reset_in': f"{int(FAILURE_RESET_TIME - time_since_last)}s" if time_since_last < FAILURE_RESET_TIME else "ready_to_reset"
        }
    
    return jsonify({
        'max_attempts': MAX_FAILED_ATTEMPTS,
        'reset_time_seconds': FAILURE_RESET_TIME,
        'failed_messages': status,
        'total_failed_messages': len(failed_attempts)
    })

@app.route('/circuit-breaker/reset', methods=['POST'])
def reset_circuit_breaker():
    """Reset circuit breaker (clear all failure records)"""
    global failed_attempts
    cleared_count = len(failed_attempts)
    failed_attempts = {}
    
    logger.info(f"Circuit breaker reset - cleared {cleared_count} failure records")
    
    return jsonify({
        'status': 'success',
        'message': f'Circuit breaker reset - cleared {cleared_count} failure records'
    })

@app.route('/processed-messages', methods=['GET'])
def processed_messages_status():
    """Get processed messages tracking status"""
    return jsonify({
        'total_processed_messages': len(processed_messages),
        'max_capacity': PROCESSED_MESSAGES_MAX_SIZE,
        'memory_usage_percent': round((len(processed_messages) / PROCESSED_MESSAGES_MAX_SIZE) * 100, 2),
        'recent_messages': list(processed_messages)[-10:] if processed_messages else []
    })

@app.route('/processed-messages/reset', methods=['POST'])
def reset_processed_messages():
    """Reset processed messages tracking (clear all records)"""
    global processed_messages
    cleared_count = len(processed_messages)
    processed_messages = set()
    
    logger.info(f"Processed messages tracking reset - cleared {cleared_count} records")
    
    return jsonify({
        'status': 'success',
        'message': f'Processed messages tracking reset - cleared {cleared_count} records'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)