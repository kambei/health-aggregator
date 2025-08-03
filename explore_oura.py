#!/usr/bin/env python3
# explore_oura.py
#
# A script to explore the OuraClient methods

import os
from dotenv import load_dotenv
from oura import OuraClient

# Load environment variables
load_dotenv()

# Get Oura token
access_token = os.environ.get('OURA_ACCESS_TOKEN')

# Initialize client
oura_client = OuraClient(access_token)

# Print available methods and attributes
print("OuraClient methods and attributes:")
print("=" * 50)
for item in dir(oura_client):
    if not item.startswith('_'):  # Skip private methods
        print(item)

# Try to get user info
print("\nTrying to get user info:")
print("=" * 50)
try:
    user_info = oura_client.user_info()
    print(f"User info: {user_info}")
except Exception as e:
    print(f"Error getting user info: {e}")

# Try to access different API endpoints
print("\nTrying to access different API endpoints:")
print("=" * 50)

# Get yesterday's date for testing
import datetime
yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

endpoints = [
    "daily_activity",
    "daily_readiness", 
    "daily_sleep",
    "heartrate",
    "personal_info",
    "sessions",
    "sleep",
    "tags",
    "workouts"
]

for endpoint in endpoints:
    print(f"\nTrying endpoint: {endpoint}")
    try:
        if hasattr(oura_client, endpoint):
            method = getattr(oura_client, endpoint)
            result = method(start=yesterday, end=yesterday)
            print(f"Success! Response structure: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        else:
            print(f"Method {endpoint} not found on OuraClient")
    except Exception as e:
        print(f"Error accessing {endpoint}: {e}")