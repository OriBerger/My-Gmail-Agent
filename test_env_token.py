#!/usr/bin/env python3
"""
Test the environment variable token functionality
"""

import os
import json
import tempfile
from app import get_credentials

def test_env_token_functionality():
    """Test that the app can create token.json from environment variable"""
    
    print("Testing environment variable token functionality...")
    
    # Read the current token.json content
    if not os.path.exists('token.json'):
        print("ERROR: token.json not found for testing")
        return False
    
    with open('token.json', 'r') as f:
        original_token = f.read()
    
    # Temporarily remove token.json
    temp_token_path = 'token.json.backup'
    os.rename('token.json', temp_token_path)
    
    try:
        # Set the environment variable
        os.environ['GMAIL_TOKEN_JSON'] = original_token
        
        # Test that get_credentials creates the file from env var
        creds = get_credentials()
        
        if creds is None:
            print("ERROR: get_credentials returned None")
            return False
        
        if not os.path.exists('token.json'):
            print("ERROR: token.json was not created from environment variable")
            return False
        
        # Verify the created file has the same JSON content (format may differ)
        with open('token.json', 'r') as f:
            created_token = f.read()
        
        try:
            original_data = json.loads(original_token)
            created_data = json.loads(created_token)
            
            if original_data == created_data:
                print("SUCCESS: token.json created correctly from environment variable")
                return True
            else:
                print("ERROR: Created token.json data doesn't match original")
                return False
        except Exception as e:
            print(f"ERROR: JSON parsing failed: {e}")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception during test: {e}")
        return False
        
    finally:
        # Clean up
        if 'GMAIL_TOKEN_JSON' in os.environ:
            del os.environ['GMAIL_TOKEN_JSON']
        
        # Restore original token.json
        if os.path.exists('token.json'):
            os.remove('token.json')
        os.rename(temp_token_path, 'token.json')

def test_without_env_var():
    """Test that the app works normally without environment variable"""
    
    print("Testing normal operation without environment variable...")
    
    # Make sure env var is not set
    if 'GMAIL_TOKEN_JSON' in os.environ:
        del os.environ['GMAIL_TOKEN_JSON']
    
    try:
        creds = get_credentials()
        
        if creds is not None:
            print("SUCCESS: Normal operation works without environment variable")
            return True
        else:
            print("INFO: No credentials available (normal for fresh setup)")
            return True
            
    except Exception as e:
        print(f"ERROR: Exception during normal operation test: {e}")
        return False

if __name__ == '__main__':
    print("ENVIRONMENT VARIABLE TOKEN TEST")
    print("=" * 40)
    
    test1_passed = test_env_token_functionality()
    print()
    test2_passed = test_without_env_var()
    
    print("\nTEST RESULTS:")
    print(f"Environment variable functionality: {'PASS' if test1_passed else 'FAIL'}")
    print(f"Normal operation: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\nSUCCESS: All tests passed!")
        print("Your app is ready for Render deployment with environment variable token!")
    else:
        print("\nFAILED: Some tests failed. Please check the implementation.")