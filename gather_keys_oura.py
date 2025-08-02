# gather_keys_oura.py
#
# A script to perform the OAuth 2.0 authorization flow for the Oura API
# and retrieve the initial access and refresh tokens.
#
# Usage:
# python gather_keys_oura.py <YOUR_OURA_CLIENT_ID> <YOUR_OURA_CLIENT_SECRET>
#
# You must have set your Redirect URI to http://127.0.0.1:8080 in your
# Oura application settings.

import os
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from requests_oauthlib import OAuth2Session

# --- Configuration ---
# The Redirect URI you've set in your Oura App settings.
REDIRECT_URI = "http://127.0.0.1:8080"
AUTHORIZATION_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"
SCOPES = ["email", "personal", "daily", "heartrate", "workout", "session", "tags"]

# This will hold the authorization code when the server receives it.
authorization_code = None

class OAuth2CallbackHandler(BaseHTTPRequestHandler):
    """A simple HTTP server to handle the OAuth2 callback."""

    def do_GET(self):
        """Handle the GET request from the browser redirect."""
        global authorization_code
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        # Send a success response to the browser
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Authorization Successful!</h1>")
        self.wfile.write(b"<p>You can close this window now.</p>")

        # Extract the code and signal the server to shut down
        if 'code' in query_params:
            authorization_code = query_params['code'][0]
        else:
            print("Error: Could not find 'code' in the callback URL.")
            # Still shut down even if there's an error
            authorization_code = "error"


def main():
    """Main function to run the authorization flow."""
    if len(sys.argv) != 3:
        print("Usage: python gather_keys_oura.py <CLIENT_ID> <CLIENT_SECRET>")
        sys.exit(1)

    client_id = sys.argv[1]
    client_secret = sys.argv[2]

    # 1. Get the authorization URL and prompt the user
    oura_session = OAuth2Session(client_id, redirect_uri=REDIRECT_URI, scope=SCOPES)
    auth_url, state = oura_session.authorization_url(AUTHORIZATION_URL)

    print("\n--- Oura API Authorization ---")
    print("Your browser will now open to authorize this application.")
    print("If it doesn't, please copy and paste this URL into your browser:")
    print(f"\n{auth_url}\n")
    webbrowser.open(auth_url)

    # 2. Start a local server to listen for the callback
    server_address = urlparse(REDIRECT_URI)
    httpd = HTTPServer((server_address.hostname, server_address.port), OAuth2CallbackHandler)
    print(f"Waiting for authorization on {REDIRECT_URI}...")

    # Wait for the single request to be handled
    while authorization_code is None:
        httpd.handle_request()

    httpd.server_close()
    print("Authorization callback received. Server shutting down.")

    if authorization_code == "error":
        print("\nFailed to retrieve authorization code.")
        sys.exit(1)

    # 3. Exchange the authorization code for an access token
    print("\nExchanging authorization code for tokens...")
    try:
        token = oura_session.fetch_token(
            TOKEN_URL,
            code=authorization_code,
            client_secret=client_secret,
            include_client_id=True
        )

        print("\n--- SUCCESS! ---")
        print("Your Oura API tokens have been generated.")
        print("Copy these into your .env file:\n")
        print(f"OURA_ACCESS_TOKEN=\"{token['access_token']}\"")
        print(f"OURA_REFRESH_TOKEN=\"{token['refresh_token']}\"")

    except Exception as e:
        print(f"\nAn error occurred while fetching the token: {e}")
        print("Please check your Client ID and Secret.")

if __name__ == "__main__":
    main()