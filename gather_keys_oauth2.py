# gather_keys_oauth2.py
#
# A script to perform the OAuth 2.0 authorization flow for the Fitbit API
# and retrieve the initial access and refresh tokens.
#
# This is a standard script provided by the python-fitbit library.
#
# Usage:
# python gather_keys_oauth2.py <YOUR_FITBIT_CLIENT_ID> <YOUR_FITBIT_CLIENT_SECRET>
#
# You must have set your Redirect URI to http://127.0.0.1:8080 in your
# Fitbit application settings.

import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from requests_oauthlib import OAuth2Session


class OAuth2Handler(BaseHTTPRequestHandler):
    """A simple HTTP server to handle the OAuth2 callback."""

    def do_GET(self):
        """Handle the GET request from the browser redirect."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Authorization Successful!</h1>")
        self.wfile.write(b"<p>You can close this browser window and return to the console.</p>")

        # Extract the authorization code from the request
        parsed_url = urlparse(self.path)
        self.server.authorization_code = parse_qs(parsed_url.query).get('code', [None])[0]


class StoppableHTTPServer(HTTPServer):
    """An HTTP server that can be stopped from a request handler."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.authorization_code = None

    def serve_forever(self, poll_interval=0.5):
        """Handle one request at a time until `authorization_code` is set."""
        while self.authorization_code is None:
            self.handle_request()


def main():
    """Main function to run the authorization flow."""
    if len(sys.argv) != 3:
        print("Usage: python gather_keys_oauth2.py <client_id> <client_secret>")
        sys.exit(1)

    client_id = sys.argv[1]
    client_secret = sys.argv[2]
    redirect_uri = 'http://127.0.0.1:8080'
    scope = ['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight']
    authorization_base_url = "https://www.fitbit.com/oauth2/authorize"
    token_url = "https://api.fitbit.com/oauth2/token"

    # 1. Create an OAuth2Session and get the authorization URL
    fitbit = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    authorization_url, state = fitbit.authorization_url(authorization_base_url)

    print("\n--- Fitbit API Authorization ---")
    print("Your browser will now open to authorize this application.")
    print("If it doesn't, please copy and paste this URL into your browser:")
    print(f"\n{authorization_url}\n")
    webbrowser.open(authorization_url)

    # 2. Start a local server to listen for the callback
    server_address = urlparse(redirect_uri)
    httpd = StoppableHTTPServer((server_address.hostname, server_address.port), OAuth2Handler)
    print(f"Waiting for authorization on {redirect_uri}...")

    # This will block until the authorization code is received
    httpd.serve_forever()

    if not httpd.authorization_code:
        print("Authorization failed. No code received.")
        sys.exit(1)

    print("Authorization callback received. Server shutting down.")

    # 3. Exchange the authorization code for an access token
    print("\nExchanging authorization code for tokens...")
    try:
        token = fitbit.fetch_token(
            token_url,
            client_secret=client_secret,
            code=httpd.authorization_code
        )

        print("\n--- SUCCESS! ---")
        print("Your Fitbit API tokens have been generated.")
        print("Copy these into your .env file:\n")
        print(f"FITBIT_ACCESS_TOKEN=\"{token['access_token']}\"")
        print(f"FITBIT_REFRESH_TOKEN=\"{token['refresh_token']}\"")

    except Exception as e:
        print(f"\nAn error occurred while fetching the token: {e}")
        print("Please check your Client ID and Secret and that the redirect URI matches.")


if __name__ == "__main__":
    main()
