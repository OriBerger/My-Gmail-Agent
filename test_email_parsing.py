#!/usr/bin/env python3
"""
Test email parsing robustness with various malformed email structures
"""

import json
import base64
from app import fetch_email_content
from unittest.mock import Mock

def create_mock_service():
    """Create a mock Gmail service for testing"""
    return Mock()

def test_normal_email():
    """Test parsing of normal email structure"""
    print("Testing normal email structure...")
    
    # Create mock email data
    email_data = {
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Subject'},
                {'name': 'From', 'value': 'test@example.com'}
            ],
            'mimeType': 'text/plain',
            'body': {
                'data': base64.urlsafe_b64encode(b'Hello, this is a test email!').decode()
            }
        }
    }
    
    # Mock service
    service = create_mock_service()
    service.users().messages().get().execute.return_value = email_data
    
    try:
        result = fetch_email_content(service, 'test_id')
        print("SUCCESS: Normal email parsed successfully")
        print(f"Result: {result[:100]}...")
        return True
    except Exception as e:
        print(f"ERROR: Normal email parsing failed: {e}")
        return False

def test_missing_payload():
    """Test email with missing payload"""
    print("Testing email with missing payload...")
    
    email_data = {}  # No payload
    
    service = create_mock_service()
    service.users().messages().get().execute.return_value = email_data
    
    try:
        result = fetch_email_content(service, 'test_id')
        print("SUCCESS: Missing payload handled gracefully")
        return True
    except Exception as e:
        print(f"ERROR: Missing payload caused crash: {e}")
        return False

def test_missing_headers():
    """Test email with missing headers"""
    print("Testing email with missing headers...")
    
    email_data = {
        'payload': {
            # No headers
            'mimeType': 'text/plain',
            'body': {
                'data': base64.urlsafe_b64encode(b'Test content').decode()
            }
        }
    }
    
    service = create_mock_service()
    service.users().messages().get().execute.return_value = email_data
    
    try:
        result = fetch_email_content(service, 'test_id')
        print("SUCCESS: Missing headers handled gracefully")
        return True
    except Exception as e:
        print(f"ERROR: Missing headers caused crash: {e}")
        return False

def test_multipart_email():
    """Test multipart email structure"""
    print("Testing multipart email...")
    
    email_data = {
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Multipart Test'},
                {'name': 'From', 'value': 'multipart@example.com'}
            ],
            'parts': [
                {
                    'mimeType': 'text/html',
                    'body': {
                        'data': base64.urlsafe_b64encode(b'<html>HTML content</html>').decode()
                    }
                },
                {
                    'mimeType': 'text/plain',
                    'body': {
                        'data': base64.urlsafe_b64encode(b'Plain text content').decode()
                    }
                }
            ]
        }
    }
    
    service = create_mock_service()
    service.users().messages().get().execute.return_value = email_data
    
    try:
        result = fetch_email_content(service, 'test_id')
        print("SUCCESS: Multipart email parsed successfully")
        return True
    except Exception as e:
        print(f"ERROR: Multipart email parsing failed: {e}")
        return False

def test_malformed_part():
    """Test email with malformed parts"""
    print("Testing email with malformed parts...")
    
    email_data = {
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Malformed Test'},
                {'name': 'From', 'value': 'malformed@example.com'}
            ],
            'parts': [
                {
                    # Missing mimeType and body
                },
                {
                    'mimeType': 'text/plain',
                    # Missing body
                }
            ]
        }
    }
    
    service = create_mock_service()
    service.users().messages().get().execute.return_value = email_data
    
    try:
        result = fetch_email_content(service, 'test_id')
        print("SUCCESS: Malformed parts handled gracefully")
        return True
    except Exception as e:
        print(f"ERROR: Malformed parts caused crash: {e}")
        return False

def test_invalid_base64():
    """Test email with invalid base64 data"""
    print("Testing email with invalid base64...")
    
    email_data = {
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Invalid Base64'},
                {'name': 'From', 'value': 'invalid@example.com'}
            ],
            'mimeType': 'text/plain',
            'body': {
                'data': 'invalid-base64-data!!!'
            }
        }
    }
    
    service = create_mock_service()
    service.users().messages().get().execute.return_value = email_data
    
    try:
        result = fetch_email_content(service, 'test_id')
        print("SUCCESS: Invalid base64 handled gracefully")
        return True
    except Exception as e:
        print(f"ERROR: Invalid base64 caused crash: {e}")
        return False

def run_all_tests():
    """Run all email parsing tests"""
    print("EMAIL PARSING ROBUSTNESS TESTS")
    print("=" * 40)
    
    tests = [
        test_normal_email,
        test_missing_payload,
        test_missing_headers,
        test_multipart_email,
        test_malformed_part,
        test_invalid_base64
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"ERROR: Test {test.__name__} crashed: {e}")
        print()
    
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: All email parsing tests passed!")
        print("Your email parsing is robust and production-ready!")
    else:
        print("WARNING: Some tests failed. Review the email parsing logic.")
    
    return passed == total

if __name__ == '__main__':
    run_all_tests()