# Health Aggregator

A Python application that fetches and compares health data from Fitbit and Oura Ring APIs, providing insights into sleep, heart rate, and stress metrics.

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install python-fitbit oura-ring pandas matplotlib python-dotenv requests-oauthlib
```

## Setup

### 1. Create API Applications

#### Fitbit API
1. Go to [https://dev.fitbit.com/](https://dev.fitbit.com/) and create a developer account
2. Register a new application
3. Set the OAuth 2.0 Redirect URL to: `http://127.0.0.1:8080`
4. Note your Client ID and Client Secret

#### Oura Ring API
1. Go to [https://cloud.ouraring.com/oauth/applications](https://cloud.ouraring.com/oauth/applications) and create a developer account
2. Register a new application
3. Set the Redirect URI to: `http://127.0.0.1:8080`
4. Note your Client ID and Client Secret

### 2. Get Access Tokens

#### Oura Ring Tokens

Run the following from your terminal, passing in your Oura Client ID and Secret:
```bash
python gather_keys_oura.py YOUR_OURA_CLIENT_ID YOUR_OURA_CLIENT_SECRET
```
This will open your browser, ask you to log in to Oura and approve access, and then print out the tokens you need.

#### Fitbit Tokens

Run the following from your terminal:
```bash
python gather_keys_oauth2.py YOUR_FITBIT_CLIENT_ID YOUR_FITBIT_CLIENT_SECRET
```
This will open your browser, ask you to log in to Fitbit and approve access, and then print out the tokens you need.

### 3. Configure Environment Variables

Create a `.env` file in the project root with the following content:

```
# --- Oura Ring API ---
OURA_CLIENT_ID="YOUR_OURA_CLIENT_ID"
OURA_CLIENT_SECRET="YOUR_OURA_CLIENT_SECRET"
OURA_ACCESS_TOKEN="YOUR_OURA_ACCESS_TOKEN"
OURA_REFRESH_TOKEN="YOUR_OURA_REFRESH_TOKEN"

# --- Fitbit API ---
FITBIT_CLIENT_ID="YOUR_FITBIT_CLIENT_ID"
FITBIT_CLIENT_SECRET="YOUR_FITBIT_CLIENT_SECRET"
FITBIT_ACCESS_TOKEN="YOUR_FITBIT_ACCESS_TOKEN"
FITBIT_REFRESH_TOKEN="YOUR_FITBIT_REFRESH_TOKEN"
```

Replace the placeholder values with your actual credentials and tokens.

## Usage

Run the main script to fetch and compare data from both Fitbit and Oura Ring:

```bash
python main.py
```

The script will:
1. Fetch sleep data from both sources
2. Fetch heart rate data from both sources
3. Fetch stress data from both sources
4. Display comparison tables in the console
5. Generate comparison charts saved as PNG files

By default, the script fetches data from yesterday. The comparison includes metrics like:
- Sleep: total sleep time, sleep efficiency, sleep stages
- Heart Rate: resting, minimum, maximum, and average heart rates
- Stress: HRV scores and stress/readiness scores

