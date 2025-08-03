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
from oura_ring import OuraClient
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth

# Load environment variables from .env file
load_dotenv()

# Get today's date and yesterday's date
today = datetime.datetime.now().strftime('%Y-%m-%d')
yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')


def refresh_fitbit_token():
    """Refreshes the Fitbit OAuth2 token and updates it in the current session's environment."""
    client_id = os.environ.get('FITBIT_CLIENT_ID')
    client_secret = os.environ.get('FITBIT_CLIENT_SECRET')
    refresh_token = os.environ.get('FITBIT_REFRESH_TOKEN')
    auth = HTTPBasicAuth(client_id, client_secret)
    fitbit_session = OAuth2Session(client_id, token={'refresh_token': refresh_token})
    new_token = fitbit_session.refresh_token(
        'https://api.fitbit.com/oauth2/token',
        refresh_token=refresh_token,
        auth=auth
    )
    os.environ['FITBIT_ACCESS_TOKEN'] = new_token['access_token']
    os.environ['FITBIT_REFRESH_TOKEN'] = new_token['refresh_token']
    print("Fitbit token refreshed successfully.")
    return new_token['access_token'], new_token['refresh_token']


def get_fitbit_client():
    """Initializes and returns an authenticated Fitbit API client."""
    try:
        client_id = os.environ.get('FITBIT_CLIENT_ID')
        client_secret = os.environ.get('FITBIT_CLIENT_SECRET')
        access_token = os.environ.get('FITBIT_ACCESS_TOKEN')
        refresh_token = os.environ.get('FITBIT_REFRESH_TOKEN')

        if not all([access_token, refresh_token, client_id, client_secret]):
            print("Error: Fitbit credentials not found in .env file.")
            sys.exit(1)

        def on_refresh(token):
            pass

        fitbit = Fitbit(
            client_id,
            client_secret,
            oauth2=True,
            access_token=access_token,
            refresh_token=refresh_token,
            refresh_cb=on_refresh
        )
        fitbit.user_profile_get()
        print("Fitbit connection successful.")

    except Exception:
        print("Fitbit token likely expired, attempting refresh...")
        try:
            new_access_token, new_refresh_token = refresh_fitbit_token()
            fitbit = Fitbit(
                client_id,
                client_secret,
                oauth2=True,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                refresh_cb=on_refresh
            )
            fitbit.user_profile_get()
            print("Fitbit connection successful with new token.")
        except Exception as e:
            print(f"Failed to refresh Fitbit token or re-initialize client: {e}")
            sys.exit(1)

    return fitbit


def get_oura_client():
    """Initializes and returns an authenticated Oura API client."""
    try:
        access_token = os.environ.get('OURA_ACCESS_TOKEN')
        if not access_token:
            print("Error: OURA_ACCESS_TOKEN not found in .env file.")
            sys.exit(1)

        oura = OuraClient(personal_access_token=access_token)
        # Using get_personal_info() for older library compatibility
        info = oura.get_personal_info()
        print(f"Oura connection successful for user: {info.get('email')}")
        return oura

    except Exception as e:
        print(f"Oura connection failed. Token may be expired or invalid: {e}")
        sys.exit(1)


def get_fitbit_sleep(fitbit_client, date=yesterday):
    """Fetches and summarizes sleep data from Fitbit for a given date."""
    try:
        sleep_data = fitbit_client.sleep(date=date)
        if not sleep_data or 'sleep' not in sleep_data or not sleep_data['sleep']:
            print(f"No Fitbit sleep data available for {date}")
            return None

        summary = {
            'date': date, 'total_minutes_asleep': 0, 'total_time_in_bed': 0,
            'efficiency': 0, 'deep_sleep_minutes': 0, 'light_sleep_minutes': 0,
            'rem_sleep_minutes': 0, 'awake_minutes': 0
        }

        for sleep_session in sleep_data['sleep']:
            summary['total_minutes_asleep'] += sleep_session.get('minutesAsleep', 0)
            summary['total_time_in_bed'] += sleep_session.get('timeInBed', 0)
            summary['efficiency'] = max(summary['efficiency'], sleep_session.get('efficiency', 0))

            if 'levels' in sleep_session and 'summary' in sleep_session['levels']:
                levels = sleep_session['levels']['summary']
                summary['deep_sleep_minutes'] += levels.get('deep', {}).get('minutes', 0)
                summary['light_sleep_minutes'] += levels.get('light', {}).get('minutes', 0)
                summary['rem_sleep_minutes'] += levels.get('rem', {}).get('minutes', 0)
                summary['awake_minutes'] += levels.get('wake', {}).get('minutes', 0)

        return summary

    except Exception as e:
        print(f"Error fetching Fitbit sleep data: {e}")
        return None


def get_oura_sleep(oura_client, date=yesterday):
    """Fetches and summarizes sleep data from Oura for a given date."""
    try:
        # Using get_daily_sleep() for older library compatibility
        sleep_docs = oura_client.get_daily_sleep(start_date=date, end_date=date)
        if not sleep_docs or 'data' not in sleep_docs or not sleep_docs['data']:
            print(f"No Oura sleep data available for {date}")
            return None

        summary = {
            'date': date, 'total_minutes_asleep': 0, 'total_time_in_bed': 0,
            'efficiency': 0, 'deep_sleep_minutes': 0, 'light_sleep_minutes': 0,
            'rem_sleep_minutes': 0, 'awake_minutes': 0
        }
        efficiency_values = []

        for session in sleep_docs['data']:
            contributors = session.get('contributors', {})
            summary['total_minutes_asleep'] += contributors.get('total_sleep', 0) // 60
            summary['total_time_in_bed'] += session.get('time_in_bed', 0) // 60
            if 'sleep_efficiency' in contributors:
                efficiency_values.append(contributors['sleep_efficiency'])
            summary['deep_sleep_minutes'] += contributors.get('deep_sleep', 0) // 60
            summary['light_sleep_minutes'] += contributors.get('light_sleep', 0) // 60
            summary['rem_sleep_minutes'] += contributors.get('rem_sleep', 0) // 60
            summary['awake_minutes'] += contributors.get('awake_time', 0) // 60

        if efficiency_values:
            summary['efficiency'] = sum(efficiency_values) / len(efficiency_values)

        return summary
    except Exception as e:
        print(f"Error fetching Oura sleep data: {e}")
        return None


def get_fitbit_heart_rate(fitbit_client, date=yesterday):
    """Fetches and summarizes heart rate data from Fitbit for a given date."""
    try:
        # intraday_time_series returns both summary and intraday data in one call
        hr_data = fitbit_client.intraday_time_series('activities/heart', base_date=date, detail_level='1min')

        if not hr_data or 'activities-heart' not in hr_data or not hr_data['activities-heart']:
            print(f"No Fitbit heart rate summary available for {date}")
            return None

        summary = {'date': date, 'resting_heart_rate': 0, 'min_heart_rate': 0, 'max_heart_rate': 0, 'avg_heart_rate': 0}

        # Resting heart rate is in the daily summary part of the response
        hr_summary = hr_data['activities-heart'][0]
        summary['resting_heart_rate'] = hr_summary.get('value', {}).get('restingHeartRate', None)

        # Min, max, and avg are calculated from the intraday dataset
        if 'activities-heart-intraday' in hr_data and 'dataset' in hr_data['activities-heart-intraday']:
            dataset = hr_data['activities-heart-intraday']['dataset']
            if dataset:
                heart_rates = [entry['value'] for entry in dataset]
                if heart_rates:
                    summary['min_heart_rate'] = min(heart_rates)
                    summary['max_heart_rate'] = max(heart_rates)
                    summary['avg_heart_rate'] = sum(heart_rates) / len(heart_rates)

        return summary

    except Exception as e:
        print(f"Error fetching Fitbit heart rate data: {e}")
        return None


def get_oura_heart_rate(oura_client, date=yesterday):
    """Fetches and summarizes heart rate data from Oura for a given date."""
    try:
        # Formato corretto per le date ISO 8601
        start_dt = f"{date}T00:00:00+00:00"
        end_dt = f"{date}T23:59:59+00:00"

        print(f"Richiesta dati Oura per la frequenza cardiaca dal {start_dt} al {end_dt}")

        # Chiamata all'API con formato corretto
        hr_data = oura_client.get_heart_rate(start_datetime=start_dt, end_datetime=end_dt)

        # Stampa la risposta per debug
        print(f"Risposta API Oura (primi 50 caratteri): {str(hr_data)[:50]}...")

        # Verifica se i dati sono nel formato atteso
        if not hr_data:
            print(f"Nessuna risposta dall'API Oura per {date}")
            return None

        # Assicuriamoci che ci sia una lista di dati nella risposta
        if isinstance(hr_data, list):
            heart_rate_data = hr_data
        elif isinstance(hr_data, dict) and 'data' in hr_data:
            heart_rate_data = hr_data['data']
        else:
            print(f"Formato di risposta Oura non riconosciuto: {type(hr_data)}")
            return None

        if not heart_rate_data:
            print(f"Nessun dato di frequenza cardiaca Oura disponibile per {date}")
            return None

        # Estrai i valori BPM dalla risposta
        heart_rates = [entry['bpm'] for entry in heart_rate_data if 'bpm' in entry]
        if not heart_rates:
            print(f"Nessun valore BPM trovato nei dati Oura per {date}")
            return None

        summary = {
            'date': date,
            'resting_heart_rate': None,
            'min_heart_rate': min(heart_rates),
            'max_heart_rate': max(heart_rates),
            'avg_heart_rate': sum(heart_rates) / len(heart_rates)
        }

        # La frequenza cardiaca a riposo si trova nei dati del sonno
        try:
            sleep_docs = oura_client.get_daily_sleep(start_date=date, end_date=date)
            print(f"Risposta dati sonno Oura (primi 50 caratteri): {str(sleep_docs)[:50]}...")

            if sleep_docs and 'data' in sleep_docs and sleep_docs['data']:
                rhr_values = []
                for sleep_session in sleep_docs['data']:
                    if 'contributors' in sleep_session and 'resting_heart_rate' in sleep_session['contributors']:
                        rhr_values.append(sleep_session['contributors']['resting_heart_rate'])

                if rhr_values:
                    summary['resting_heart_rate'] = min(rhr_values)
                    print(f"Valori di frequenza cardiaca a riposo trovati: {rhr_values}")
                else:
                    print("Nessun valore di frequenza cardiaca a riposo trovato nei dati del sonno")
        except Exception as sleep_e:
            print(f"Errore nel recupero dei dati del sonno Oura: {sleep_e}")

        return summary
    except Exception as e:
        print(f"Errore nel recupero dei dati della frequenza cardiaca Oura: {e}")
        # Stampa un traceback dettagliato per il debug
        import traceback
        traceback.print_exc()
        return None

def get_fitbit_stress(fitbit_client, date=yesterday):
    """Placeholder for Fitbit stress data."""
    return {'date': date, 'hrv_score': 0, 'stress_score': 0}


def get_oura_stress(oura_client, date=yesterday):
    """Fetches stress data from Oura, which includes stress metrics."""
    try:
        print(f"Richiesta dati Oura per lo stress in data {date}")

        # Utilizzare get_daily_stress anziché get_daily_readiness
        stress_docs = oura_client.get_daily_stress(start_date=date, end_date=date)

        # Stampa di debug
        print(f"Risposta API Oura stress (primi 50 caratteri): {str(stress_docs)[:50]}...")

        summary = {'date': date, 'hrv_score': 0, 'stress_score': 0, 'stress_high': 0, 'recovery_high': 0,
                   'day_summary': ''}

        # Adattamento in base al formato della risposta
        if isinstance(stress_docs, list):
            stress_data = stress_docs
        elif isinstance(stress_docs, dict) and 'data' in stress_docs:
            stress_data = stress_docs['data']
        else:
            print(f"Formato di risposta Oura stress non riconosciuto: {type(stress_docs)}")
            # Recuperiamo i dati di readiness come fallback
            return get_oura_readiness(oura_client, date)

        if not stress_data:
            print(f"Nessun dato di stress Oura disponibile per {date}")
            # Recuperiamo i dati di readiness come fallback
            return get_oura_readiness(oura_client, date)

        # Elaborazione della risposta get_daily_stress
        for stress_day in stress_data:
            if stress_day.get('day') == date:
                summary['stress_high'] = stress_day.get('stress_high', 0)
                summary['recovery_high'] = stress_day.get('recovery_high', 0)
                summary['day_summary'] = stress_day.get('day_summary', '')

                # Calcoliamo uno stress score basato sui valori disponibili
                # Se stress_high è alto, lo stress_score sarà basso e viceversa
                if 'stress_high' in stress_day and 'recovery_high' in stress_day:
                    stress_high = stress_day['stress_high']
                    recovery_high = stress_day['recovery_high']

                    # Formula per convertire in uno score (da 0 a 100):
                    # 100 - stress_high*100 + recovery_high*100
                    stress_score = max(0, min(100, 100 - (stress_high * 100) + (recovery_high * 100)))
                    summary['stress_score'] = int(stress_score)

        # Recuperiamo i dati HRV dal readiness
        readiness_data = get_oura_readiness(oura_client, date)
        if readiness_data and 'hrv_score' in readiness_data:
            summary['hrv_score'] = readiness_data['hrv_score']

        return summary
    except Exception as e:
        print(f"Errore nel recupero dei dati di stress Oura: {e}")
        import traceback
        traceback.print_exc()

        # Tentiamo di recuperare almeno i dati di readiness come fallback
        try:
            return get_oura_readiness(oura_client, date)
        except:
            return {'date': date, 'hrv_score': 0, 'stress_score': 0}

def get_oura_readiness(oura_client, date=yesterday):
    """Fetches readiness data from Oura, which includes HRV and readiness scores."""
    try:
        # Using get_daily_readiness() for older library compatibility
        readiness_docs = oura_client.get_daily_readiness(start_date=date, end_date=date)
        summary = {'date': date, 'hrv_score': 0, 'stress_score': 0}

        if readiness_docs and 'data' in readiness_docs and readiness_docs['data']:
            readiness = readiness_docs['data'][0]
            summary['stress_score'] = readiness.get('score', 0)

            contributors = readiness.get('contributors', {})
            summary['hrv_score'] = contributors.get('hrv_balance', 0)

        return summary
    except Exception as e:
        print(f"Error fetching Oura readiness data: {e}")
        return None

def compare_data(fitbit_data, oura_data, data_type):
    """Generates a comparison table and bar chart for a single day's data."""
    if not fitbit_data or not oura_data:
        print(f"\nCannot compare {data_type} data: missing data from one or both sources.")
        return

    print(f"\n--- {data_type.upper()} DATA COMPARISON ---")
    print(f"Date: {fitbit_data['date']}")

    df = pd.DataFrame({
        'Metric': list(fitbit_data.keys())[1:],
        'Fitbit': list(fitbit_data.values())[1:],
        'Oura': [oura_data.get(key, 'N/A') for key in list(fitbit_data.keys())[1:]]
    })

    def calculate_diff(row):
        try:
            return float(row['Fitbit']) - float(row['Oura'])
        except (ValueError, TypeError):
            return 'N/A'

    df['Difference'] = df.apply(calculate_diff, axis=1)

    pd.set_option('display.width', 1000)
    print(df.to_string(index=False, float_format="%.2f"))

    if not os.path.exists('./data'):
        os.makedirs('./data')

    plot_df = df.copy()
    plot_df['Fitbit'] = pd.to_numeric(plot_df['Fitbit'], errors='coerce')
    plot_df['Oura'] = pd.to_numeric(plot_df['Oura'], errors='coerce')
    plot_df.dropna(subset=['Fitbit', 'Oura'], how='all', inplace=True)

    if not plot_df.empty:
        ax = plot_df.plot(x='Metric', y=['Fitbit', 'Oura'], kind='bar', figsize=(12, 7),
                          title=f'{data_type.title()} Data Comparison for {yesterday}')
        ax.set_ylabel('Values')
        ax.set_xlabel('Metrics')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        filename = f"./data/{data_type.lower().replace(' ', '_')}_comparison_{yesterday}.png"
        plt.savefig(filename)
        print(f"\nChart saved as {filename}")
        plt.close()


def plot_aggregated_data(aggregated_data):
    """Creates a line chart to show trends over a date range."""
    if not aggregated_data:
        print("No aggregated data to plot.")
        return

    df = pd.DataFrame(aggregated_data)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    # Exit if DataFrame is empty after processing
    if df.empty or df[['fitbit_resting_hr', 'oura_resting_hr']].isnull().all().all():
        print("No numeric data available to plot trends. Check API fetch errors.")
        return

    # Aumenta il numero di righe da 2 a 3 per aggiungere il grafico dello stress
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(15, 15), sharex=True)
    fig.suptitle('Health Metrics Over Time', fontsize=16)

    # Grafico 1: Frequenza cardiaca a riposo
    df[['fitbit_resting_hr', 'oura_resting_hr']].plot(ax=axes[0], marker='o', linestyle='-')
    axes[0].set_title('Resting Heart Rate')
    axes[0].set_ylabel('BPM')
    axes[0].grid(True, which='both', linestyle='--', linewidth=0.5)
    axes[0].legend(['Fitbit', 'Oura'])

    # Grafico 2: HRV Score di Oura
    df[['oura_hrv_score']].plot(ax=axes[1], marker='o', linestyle='-', color='orange')
    axes[1].set_title('Oura HRV Balance Score')
    axes[1].set_ylabel('Score')
    axes[1].grid(True, which='both', linestyle='--', linewidth=0.5)
    axes[1].legend(['Oura'])

    # Grafico 3: Stress metrics
    stress_plot_data = df[['oura_stress_score']].copy()

    # Aggiungiamo altri indicatori di stress se disponibili
    has_detailed_stress = False
    if 'oura_stress_high' in df.columns and not df['oura_stress_high'].isnull().all():
        stress_plot_data['stress_high_pct'] = df['oura_stress_high'] * 100
        has_detailed_stress = True

    if 'oura_recovery_high' in df.columns and not df['oura_recovery_high'].isnull().all():
        stress_plot_data['recovery_high_pct'] = df['oura_recovery_high'] * 100
        has_detailed_stress = True

    # Plot del grafico dello stress
    stress_plot_data.plot(ax=axes[2], marker='o', linestyle='-')
    axes[2].set_title('Oura Stress Metrics')
    axes[2].set_ylabel('Value')
    axes[2].set_xlabel('Date')
    axes[2].grid(True, which='both', linestyle='--', linewidth=0.5)

    # Adattiamo la legenda in base ai dati disponibili
    if has_detailed_stress:
        axes[2].legend(['Stress Score', 'Stress High %', 'Recovery High %'])
    else:
        axes[2].legend(['Stress Score'])

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    if not os.path.exists('./data'):
        os.makedirs('./data')
    filename = "./data/aggregated_trends_comparison.png"
    plt.savefig(filename)
    print(f"\nAggregated trend chart saved as {filename}")
    plt.close()

def main():
    """Main function to fetch, compare, and plot health data."""
    print("Health Aggregator - Comparing Fitbit and Oura Ring Data")
    print("=" * 60)

    end_date = datetime.datetime.now() - datetime.timedelta(days=1)
    start_date = end_date - datetime.timedelta(days=7)

    fitbit_client = get_fitbit_client()
    oura_client = get_oura_client()

    print("\n[1] Fetching detailed data for yesterday for direct comparison...")
    fitbit_sleep = get_fitbit_sleep(fitbit_client, yesterday)
    oura_sleep = get_oura_sleep(oura_client, yesterday)
    compare_data(fitbit_sleep, oura_sleep, 'Sleep')

    fitbit_hr = get_fitbit_heart_rate(fitbit_client, yesterday)
    oura_hr = get_oura_heart_rate(oura_client, yesterday)
    compare_data(fitbit_hr, oura_hr, 'Heart Rate')

    print(
        f"\n[2] Fetching aggregated data for trends from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    all_data = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"   - Processing data for: {date_str}")

        fitbit_hr_agg = get_fitbit_heart_rate(fitbit_client, date_str)
        oura_hr_agg = get_oura_heart_rate(oura_client, date_str)
        oura_stress_agg = get_oura_stress(oura_client, date_str)

        daily_summary = {
            'date': date_str,
            'fitbit_resting_hr': fitbit_hr_agg.get('resting_heart_rate', None) if fitbit_hr_agg else None,
            'oura_resting_hr': oura_hr_agg.get('resting_heart_rate', None) if oura_hr_agg else None,
            'oura_hrv_score': oura_stress_agg.get('hrv_score', None) if oura_stress_agg else None,
            'oura_stress_score': oura_stress_agg.get('stress_score', None) if oura_stress_agg else None,
            'oura_stress_high': oura_stress_agg.get('stress_high', None) if oura_stress_agg else None,
            'oura_recovery_high': oura_stress_agg.get('recovery_high', None) if oura_stress_agg else None,
        }
        all_data.append(daily_summary)
        current_date += datetime.timedelta(days=1)

    plot_aggregated_data(all_data)

    print("\nData aggregation and plotting complete!")


if __name__ == "__main__":
    main()