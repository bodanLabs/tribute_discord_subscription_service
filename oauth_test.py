import stripe
from flask import Flask, request, redirect, url_for, session
import os
from db_utils import save_stripe_account

# Load environment variables from .env (ensure you have Flask, stripe, and python-dotenv installed)
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Set the secret key (make sure this is unique and kept secret)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')  # Replace 'supersecretkey' with a real random key


# Stripe API keys
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Client ID for OAuth (from your Stripe Connect settings)
CLIENT_ID = os.getenv('STRIPE_CLIENT_ID')

@app.route('/')
def home():
    return '<a href="/connect">Connect with Stripe</a>'

# Route to initiate the OAuth process
@app.route('/connect')
def connect():
    # Simulate getting the actual Discord server ID (you would get this from the bot context)
    discord_server_id = '1234567890'  # Replace this with actual server ID from the bot

    # Store the Discord server ID in the session
    session['discord_server_id'] = discord_server_id

    # Redirect the user to Stripe's OAuth authorization page
    return redirect(f'https://connect.stripe.com/oauth/authorize?response_type=code&client_id={CLIENT_ID}&scope=read_write')

# Stripe OAuth callback route
@app.route('/oauth/callback')
def oauth_callback():
    # Retrieve the Discord server ID from the session
    discord_server_id = session.get('discord_server_id')

    # If the session is missing, ask the user to retry
    if discord_server_id is None:
        return "Error: Session expired. Please restart the process.", 400
    # Get the authorization code from the URL
    code = request.args.get('code')

    # Exchange the authorization code for an access token
    token_response = stripe.OAuth.token(
        grant_type='authorization_code',
        code=code
    )

    # Extract the connected Stripe account ID
    stripe_account_id = token_response['stripe_user_id']

    # Retrieve the Discord server ID from the session
    discord_server_id = session.get('discord_server_id')

    # Check if the discord_server_id exists in the session
    if discord_server_id is None:
        return "Error: Discord server ID is missing from session", 400

    # Save the Discord server ID and Stripe account ID to the database
    save_stripe_account(discord_server_id, stripe_account_id)

    return f"Success! Connected Stripe Account ID: {stripe_account_id}"


if __name__ == "__main__":
    app.run(port=5000, debug=True)
