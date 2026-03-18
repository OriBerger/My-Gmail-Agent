#!/usr/bin/env python3
"""
Debug token environment variable issue
"""

import os
import json

# Read original token
with open('token.json', 'r') as f:
    original = f.read()

print("Original token length:", len(original))
print("Original token (first 100 chars):", original[:100])

# Test JSON parsing
try:
    parsed = json.loads(original)
    print("Original token is valid JSON")
except Exception as e:
    print(f"Original token JSON error: {e}")

# Test the minified version from our script
minified = json.dumps(json.loads(original), separators=(',', ':'))
print("Minified token length:", len(minified))
print("Minified token (first 100 chars):", minified[:100])

print("Are they equal?", original.strip() == minified)