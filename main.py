#!/usr/bin/env python3
# main.py
#
# A Python script to fetch data from the Oura and Fitbit APIs and compare health metrics.
#
# Installation:
# pip install python-fitbit oura-ring pandas matplotlib python-dotenv requests-oauthlib
#

import os
import sys
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from fitbit import Fitbit
from oura import OuraClient
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth

# Load environment variables from .env file
load_dotenv()

# Get today's date and yesterday's date
today = datetime.datetime.now().strftime('%Y-%m-%d')
yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

# Function to refresh Fitbit token if needed
def refresh_fitbit_token():
    client_id = os.environ.get('FITBIT_CLIENT_ID')
    client_secret = os.environ.get('FITBIT_CLIENT_SECRET')
    refresh_token = os.environ.get('FITBIT_REFRESH_TOKEN')
    
    auth = HTTPBasicAuth(client_id, client_secret)
    refresh_callback = {
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    fitbit_session = OAuth2Session(client_id, token={'refresh_token': refresh_token})
    new_token = fitbit_session.refresh_token(
        'https://api.fitbit.com/oauth2/token',
        refresh_token=refresh_token,
        auth=auth
    )
    
    # Update environment variables with new tokens
    os.environ['FITBIT_ACCESS_TOKEN'] = new_token['access_token']
    os.environ['FITBIT_REFRESH_TOKEN'] = new_token['refresh_token']
    
    print("Fitbit token refreshed successfully.")
    return new_token['access_token']

# Function to refresh Oura token if needed
def refresh_oura_token():
    client_id = os.environ.get('OURA_CLIENT_ID')
    client_secret = os.environ.get('OURA_CLIENT_SECRET')
    refresh_token = os.environ.get('OURA_REFRESH_TOKEN')
    
    oura_session = OAuth2Session(client_id)
    new_token = oura_session.refresh_token(
        'https://api.ouraring.com/oauth/token',
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Update environment variables with new tokens
    os.environ['OURA_ACCESS_TOKEN'] = new_token['access_token']
    os.environ['OURA_REFRESH_TOKEN'] = new_token['refresh_token']
    
    print("Oura token refreshed successfully.")
    return new_token['access_token']

# Initialize Fitbit client
def get_fitbit_client():
    try:
        access_token = os.environ.get('FITBIT_ACCESS_TOKEN')
        refresh_token = os.environ.get('FITBIT_REFRESH_TOKEN')
        client_id = os.environ.get('FITBIT_CLIENT_ID')
        client_secret = os.environ.get('FITBIT_CLIENT_SECRET')
        
        if not all([access_token, refresh_token, client_id, client_secret]):
            print("Error: Fitbit credentials not found in .env file.")
            print("Please run 'python gather_keys_oauth2.py YOUR_FITBIT_CLIENT_ID YOUR_FITBIT_CLIENT_SECRET' first.")
            sys.exit(1)
        
        # Initialize with current token
        fitbit = Fitbit(
            client_id,
            client_secret,
            oauth2=True,
            access_token=access_token,
            refresh_token=refresh_token,
            refresh_cb=lambda x: None  # We'll handle refresh manually
        )
        
        # Test the connection
        try:
            fitbit.user_profile_get()
            print("Fitbit connection successful.")
        except Exception as e:
            print(f"Fitbit token expired, refreshing: {e}")
            new_access_token = refresh_fitbit_token()
            fitbit = Fitbit(
                client_id,
                client_secret,
                oauth2=True,
                access_token=new_access_token,
                refresh_token=os.environ.get('FITBIT_REFRESH_TOKEN'),
                refresh_cb=lambda x: None
            )
        
        return fitbit
    
    except Exception as e:
        print(f"Error initializing Fitbit client: {e}")
        sys.exit(1)

# Initialize Oura client
def get_oura_client():
    try:
        access_token = os.environ.get('OURA_ACCESS_TOKEN')
        refresh_token = os.environ.get('OURA_REFRESH_TOKEN')
        client_id = os.environ.get('OURA_CLIENT_ID')
        client_secret = os.environ.get('OURA_CLIENT_SECRET')
        
        if not all([access_token, refresh_token, client_id, client_secret]):
            print("Error: Oura credentials not found in .env file.")
            print("Please run 'python gather_keys_oura.py YOUR_OURA_CLIENT_ID YOUR_OURA_CLIENT_SECRET' first.")
            sys.exit(1)
        
        # Initialize with current token
        oura = OuraClient(access_token)
        
        # Test the connection
        try:
            oura.user_info()
            print("Oura connection successful.")
        except Exception as e:
            print(f"Oura token expired, refreshing: {e}")
            new_access_token = refresh_oura_token()
            oura = OuraClient(new_access_token)
        
        return oura
    
    except Exception as e:
        print(f"Error initializing Oura client: {e}")
        sys.exit(1)

# Fetch sleep data from Fitbit
def get_fitbit_sleep(fitbit_client, date=yesterday):
    try:
        sleep_data = fitbit_client.sleep(date=date)
        
        if not sleep_data or 'sleep' not in sleep_data or not sleep_data['sleep']:
            print(f"No Fitbit sleep data available for {date}")
            return None
        
        # Extract relevant sleep metrics
        sleep_summary = {
            'date': date,
            'total_minutes_asleep': 0,
            'total_time_in_bed': 0,
            'efficiency': 0,
            'deep_sleep_minutes': 0,
            'light_sleep_minutes': 0,
            'rem_sleep_minutes': 0,
            'awake_minutes': 0
        }
        
        # Sum up data from all sleep sessions for the day
        for sleep_session in sleep_data['sleep']:
            sleep_summary['total_minutes_asleep'] += sleep_session.get('minutesAsleep', 0)
            sleep_summary['total_time_in_bed'] += sleep_session.get('timeInBed', 0)
            
            # Get sleep efficiency if available
            if 'efficiency' in sleep_session:
                sleep_summary['efficiency'] = max(sleep_summary['efficiency'], sleep_session['efficiency'])
            
            # Get sleep stages if available
            if 'levels' in sleep_session and 'summary' in sleep_session['levels']:
                summary = sleep_session['levels']['summary']
                sleep_summary['deep_sleep_minutes'] += summary.get('deep', {}).get('minutes', 0)
                sleep_summary['light_sleep_minutes'] += summary.get('light', {}).get('minutes', 0)
                sleep_summary['rem_sleep_minutes'] += summary.get('rem', {}).get('minutes', 0)
                sleep_summary['awake_minutes'] += summary.get('wake', {}).get('minutes', 0)
        
        return sleep_summary
    
    except Exception as e:
        print(f"Error fetching Fitbit sleep data: {e}")
        return None

# Fetch sleep data from Oura
def get_oura_sleep(oura_client, date=yesterday):
    try:
        sleep_data = oura_client.sleep_summary(start=date, end=date)
        
        if not sleep_data or 'sleep' not in sleep_data or not sleep_data['sleep']:
            print(f"No Oura sleep data available for {date}")
            return None
        
        # Extract the sleep summary for the day
        sleep_summary = sleep_data['sleep'][0]
        
        # Format the data to match our structure
        formatted_summary = {
            'date': date,
            'total_minutes_asleep': sleep_summary.get('total', 0),
            'total_time_in_bed': sleep_summary.get('duration', 0) // 60,  # Convert from seconds to minutes
            'efficiency': sleep_summary.get('efficiency', 0),
            'deep_sleep_minutes': sleep_summary.get('deep', 0),
            'light_sleep_minutes': sleep_summary.get('light', 0),
            'rem_sleep_minutes': sleep_summary.get('rem', 0),
            'awake_minutes': sleep_summary.get('awake', 0)
        }
        
        return formatted_summary
    
    except Exception as e:
        print(f"Error fetching Oura sleep data: {e}")
        return None

# Fetch heart rate data from Fitbit
def get_fitbit_heart_rate(fitbit_client, date=yesterday):
    try:
        heart_data = fitbit_client.intraday_time_series('activities/heart', base_date=date, detail_level='1min')
        
        if not heart_data or 'activities-heart' not in heart_data or not heart_data['activities-heart']:
            print(f"No Fitbit heart rate data available for {date}")
            return None
        
        # Extract the heart rate zones and resting heart rate
        heart_summary = heart_data['activities-heart'][0]
        zones = heart_summary.get('value', {}).get('heartRateZones', [])
        
        heart_rate_summary = {
            'date': date,
            'resting_heart_rate': heart_summary.get('value', {}).get('restingHeartRate', 0),
            'min_heart_rate': 0,
            'max_heart_rate': 0,
            'avg_heart_rate': 0
        }
        
        # Calculate min, max, and average heart rate from intraday data
        if 'activities-heart-intraday' in heart_data and 'dataset' in heart_data['activities-heart-intraday']:
            dataset = heart_data['activities-heart-intraday']['dataset']
            if dataset:
                heart_rates = [entry['value'] for entry in dataset if 'value' in entry]
                if heart_rates:
                    heart_rate_summary['min_heart_rate'] = min(heart_rates)
                    heart_rate_summary['max_heart_rate'] = max(heart_rates)
                    heart_rate_summary['avg_heart_rate'] = sum(heart_rates) / len(heart_rates)
        
        return heart_rate_summary
    
    except Exception as e:
        print(f"Error fetching Fitbit heart rate data: {e}")
        return None

# Fetch heart rate data from Oura
def get_oura_heart_rate(oura_client, date=yesterday):
    try:
        heart_data = oura_client.heartrate(start=date, end=date)
        
        if not heart_data or 'heartrate' not in heart_data or not heart_data['heartrate']:
            print(f"No Oura heart rate data available for {date}")
            return None
        
        # Extract heart rate values
        heart_rates = [entry['bpm'] for entry in heart_data['heartrate'] if 'bpm' in entry]
        
        if not heart_rates:
            print(f"No Oura heart rate values found for {date}")
            return None
        
        # Get the daily heart rate summary
        heart_rate_summary = {
            'date': date,
            'resting_heart_rate': 0,  # Oura doesn't provide this directly
            'min_heart_rate': min(heart_rates),
            'max_heart_rate': max(heart_rates),
            'avg_heart_rate': sum(heart_rates) / len(heart_rates)
        }
        
        # Try to get resting heart rate from sleep data
        try:
            sleep_data = oura_client.sleep_summary(start=date, end=date)
            if sleep_data and 'sleep' in sleep_data and sleep_data['sleep']:
                heart_rate_summary['resting_heart_rate'] = sleep_data['sleep'][0].get('hr_lowest', 0)
        except:
            pass
        
        return heart_rate_summary
    
    except Exception as e:
        print(f"Error fetching Oura heart rate data: {e}")
        return None

# Fetch stress data from Fitbit (HRV and stress score if available)
def get_fitbit_stress(fitbit_client, date=yesterday):
    try:
        # Fitbit provides HRV data which can be an indicator of stress
        hrv_data = fitbit_client.get_hrv(date)
        
        stress_summary = {
            'date': date,
            'hrv_score': 0,
            'stress_score': 0  # Fitbit doesn't provide a direct stress score
        }
        
        if hrv_data and 'hrv' in hrv_data and hrv_data['hrv']:
            # Extract the daily HRV summary
            daily_hrv = hrv_data['hrv'][0]
            if 'value' in daily_hrv and 'dailyRmssd' in daily_hrv['value']:
                stress_summary['hrv_score'] = daily_hrv['value']['dailyRmssd']
        
        # Try to get stress score from Readiness Score if available (Premium feature)
        try:
            readiness = fitbit_client.get_readiness_score(date)
            if readiness and 'readiness' in readiness and readiness['readiness']:
                stress_summary['stress_score'] = readiness['readiness'][0].get('value', {}).get('stressBalance', 0)
        except:
            pass
        
        return stress_summary
    
    except Exception as e:
        print(f"Error fetching Fitbit stress data: {e}")
        return None

# Fetch stress data from Oura (HRV and readiness)
def get_oura_stress(oura_client, date=yesterday):
    try:
        # Oura provides HRV data and readiness score
        readiness_data = oura_client.readiness_summary(start=date, end=date)
        
        stress_summary = {
            'date': date,
            'hrv_score': 0,
            'stress_score': 0  # We'll use readiness as a proxy
        }
        
        if readiness_data and 'readiness' in readiness_data and readiness_data['readiness']:
            readiness = readiness_data['readiness'][0]
            stress_summary['stress_score'] = readiness.get('score', 0)
        
        # Get HRV from sleep data
        sleep_data = oura_client.sleep_summary(start=date, end=date)
        if sleep_data and 'sleep' in sleep_data and sleep_data['sleep']:
            sleep = sleep_data['sleep'][0]
            stress_summary['hrv_score'] = sleep.get('rmssd', 0)
        
        return stress_summary
    
    except Exception as e:
        print(f"Error fetching Oura stress data: {e}")
        return None

# Compare and display data
def compare_data(fitbit_data, oura_data, data_type):
    if not fitbit_data or not oura_data:
        print(f"Cannot compare {data_type} data: missing data from one or both sources.")
        return
    
    print(f"\n--- {data_type.upper()} DATA COMPARISON ---")
    print(f"Date: {fitbit_data['date']}")
    
    # Create a DataFrame for easy comparison
    comparison_df = pd.DataFrame({
        'Metric': list(fitbit_data.keys())[1:],  # Skip the date
        'Fitbit': [fitbit_data[key] for key in list(fitbit_data.keys())[1:]],
        'Oura': [oura_data.get(key, 'N/A') for key in list(fitbit_data.keys())[1:]]
    })
    
    # Calculate differences and percentages
    comparison_df['Difference'] = comparison_df.apply(
        lambda row: row['Fitbit'] - row['Oura'] if isinstance(row['Oura'], (int, float)) else 'N/A', 
        axis=1
    )
    
    comparison_df['% Difference'] = comparison_df.apply(
        lambda row: (abs(row['Difference']) / ((row['Fitbit'] + row['Oura']) / 2) * 100) 
                    if isinstance(row['Difference'], (int, float)) and (row['Fitbit'] + row['Oura']) > 0 
                    else 'N/A',
        axis=1
    )
    
    # Print the comparison table
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(comparison_df.to_string(index=False))
    
    # Create a bar chart for visual comparison
    metrics = list(fitbit_data.keys())[1:]  # Skip the date
    fitbit_values = [fitbit_data[key] for key in metrics]
    oura_values = [oura_data.get(key, 0) for key in metrics]
    
    # Only plot numeric values
    valid_indices = [i for i, (f, o) in enumerate(zip(fitbit_values, oura_values)) 
                    if isinstance(f, (int, float)) and isinstance(o, (int, float))]
    
    if valid_indices:
        plot_metrics = [metrics[i] for i in valid_indices]
        plot_fitbit = [fitbit_values[i] for i in valid_indices]
        plot_oura = [oura_values[i] for i in valid_indices]
        
        x = range(len(plot_metrics))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar([i - width/2 for i in x], plot_fitbit, width, label='Fitbit')
        ax.bar([i + width/2 for i in x], plot_oura, width, label='Oura')
        
        ax.set_ylabel('Values')
        ax.set_title(f'{data_type.title()} Data Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(plot_metrics, rotation=45, ha='right')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(f"./data/{data_type.lower()}_comparison.png")
        print(f"\nChart saved as ./data/{data_type.lower()}_comparison.png")

def main():
    print("Health Aggregator - Comparing Fitbit and Oura Ring Data")
    print("=" * 60)
    
    # Initialize clients
    fitbit_client = get_fitbit_client()
    oura_client = get_oura_client()
    
    # Get yesterday's date for data retrieval
    date = yesterday
    print(f"\nFetching data for: {date}")
    
    # Fetch and compare sleep data
    fitbit_sleep = get_fitbit_sleep(fitbit_client, date)
    oura_sleep = get_oura_sleep(oura_client, date)
    compare_data(fitbit_sleep, oura_sleep, "sleep")
    
    # Fetch and compare heart rate data
    fitbit_hr = get_fitbit_heart_rate(fitbit_client, date)
    oura_hr = get_oura_heart_rate(oura_client, date)
    compare_data(fitbit_hr, oura_hr, "heart rate")
    
    # Fetch and compare stress data
    fitbit_stress = get_fitbit_stress(fitbit_client, date)
    oura_stress = get_oura_stress(oura_client, date)
    compare_data(fitbit_stress, oura_stress, "stress")
    
    print("\nData comparison complete!")
    print("Charts have been saved to the ./data/ folder.")

if __name__ == "__main__":
    main()