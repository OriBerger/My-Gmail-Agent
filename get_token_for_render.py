#!/usr/bin/env python3
"""
Helper script to get token.json content for Render environment variable
"""

import os
import json

def get_token_content():
    """Get the token.json content formatted for environment variable"""
    
    if not os.path.exists('token.json'):
        print("ERROR: token.json file not found!")
        print("Please make sure you have authenticated first by running:")
        print("python test_auth.py")
        return None
    
    try:
        with open('token.json', 'r') as f:
            token_data = json.load(f)
        
        # Convert back to JSON string (minified)
        token_json_string = json.dumps(token_data, separators=(',', ':'))
        
        print("SUCCESS: Token content ready for Render!")
        print("=" * 50)
        print("COPY THE FOLLOWING TEXT:")
        print("=" * 50)
        print(token_json_string)
        print("=" * 50)
        print()
        print("INSTRUCTIONS FOR RENDER:")
        print("1. Go to your Render dashboard")
        print("2. Select your Gmail Agent service")
        print("3. Go to Environment tab")
        print("4. Add new environment variable:")
        print("   - Key: GMAIL_TOKEN_JSON")
        print("   - Value: [paste the text above]")
        print("5. Save and redeploy")
        print()
        print("SECURITY NOTE:")
        print("This token contains sensitive authentication data.")
        print("Never share it publicly or commit it to version control.")
        
        return token_json_string
        
    except Exception as e:
        print(f"ERROR: Error reading token.json: {e}")
        return None

def validate_token_format():
    """Validate that the token has the required fields"""
    
    if not os.path.exists('token.json'):
        return False
    
    try:
        with open('token.json', 'r') as f:
            token_data = json.load(f)
        
        required_fields = ['token', 'refresh_token', 'client_id', 'client_secret']
        missing_fields = [field for field in required_fields if field not in token_data]
        
        if missing_fields:
            print(f"WARNING: Token is missing required fields: {missing_fields}")
            return False
        
        print("SUCCESS: Token format is valid")
        return True
        
    except Exception as e:
        print(f"ERROR: Error validating token: {e}")
        return False

if __name__ == '__main__':
    print("Gmail Token Extractor for Render")
    print()
    
    if validate_token_format():
        token_content = get_token_content()
        
        if token_content:
            print("\nSUCCESS: Token is ready for Render deployment!")
        else:
            print("\nFAILED: Could not extract token content")
    else:
        print("\nFAILED: Token validation failed")
        print("Please re-authenticate using: python test_auth.py")