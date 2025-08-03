#!/usr/bin/env python3
# test_api.py
#
# A simple script to test the API changes
#

import os
import sys
import datetime
from dotenv import load_dotenv
from main import (
    get_fitbit_client, get_oura_client,
    get_fitbit_sleep, get_oura_sleep,
    get_fitbit_heart_rate, get_oura_heart_rate,
    get_fitbit_stress, get_oura_stress,
    get_hrv
)

# Load environment variables
load_dotenv()

# Get yesterday's date for testing
yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

def test_apis():
    print("Testing API connections and data retrieval...")
    print("=" * 60)
    
    # Initialize clients
    print("\nInitializing clients:")
    try:
        fitbit_client = get_fitbit_client()
        print("✓ Fitbit client initialized successfully")
    except Exception as e:
        print(f"✗ Fitbit client initialization failed: {e}")
        return
    
    try:
        oura_client = get_oura_client()
        print("✓ Oura client initialized successfully")
    except Exception as e:
        print(f"✗ Oura client initialization failed: {e}")
        return
    
    # Test data retrieval functions
    print("\nTesting data retrieval for date:", yesterday)
    
    # Test sleep data
    print("\n1. Testing sleep data:")
    try:
        fitbit_sleep = get_fitbit_sleep(fitbit_client, yesterday)
        print(f"✓ Fitbit sleep data: {fitbit_sleep is not None}")
    except Exception as e:
        print(f"✗ Fitbit sleep data retrieval failed: {e}")
    
    try:
        oura_sleep = get_oura_sleep(oura_client, yesterday)
        print(f"✓ Oura sleep data: {oura_sleep is not None}")
    except Exception as e:
        print(f"✗ Oura sleep data retrieval failed: {e}")
    
    # Test heart rate data
    print("\n2. Testing heart rate data:")
    try:
        fitbit_hr = get_fitbit_heart_rate(fitbit_client, yesterday)
        print(f"✓ Fitbit heart rate data: {fitbit_hr is not None}")
    except Exception as e:
        print(f"✗ Fitbit heart rate data retrieval failed: {e}")
    
    try:
        oura_hr = get_oura_heart_rate(oura_client, yesterday)
        print(f"✓ Oura heart rate data: {oura_hr is not None}")
    except Exception as e:
        print(f"✗ Oura heart rate data retrieval failed: {e}")
    
    # Test stress data
    print("\n3. Testing stress data:")
    try:
        # Test the custom get_hrv function
        hrv_data = get_hrv(fitbit_client, yesterday)
        print(f"✓ Fitbit HRV function: {hrv_data is not None}")
        
        fitbit_stress = get_fitbit_stress(fitbit_client, yesterday)
        print(f"✓ Fitbit stress data: {fitbit_stress is not None}")
    except Exception as e:
        print(f"✗ Fitbit stress data retrieval failed: {e}")
    
    try:
        oura_stress = get_oura_stress(oura_client, yesterday)
        print(f"✓ Oura stress data: {oura_stress is not None}")
    except Exception as e:
        print(f"✗ Oura stress data retrieval failed: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_apis()