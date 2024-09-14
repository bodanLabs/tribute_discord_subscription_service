import stripe
import os
from flask import Flask, request, redirect, session, url_for
from dotenv import load_dotenv
import sqlite3

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # Generate a secret key for your session

# Stripe keys
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# OAuth Client ID from Stripe Dashboard
CLIENT_ID = os.getenv('STRIPE_CLIENT_ID')


@app.route('/')
def index():
    return '<a href="/connect">Connect with Stripe</a>'


# Route to start OAuth flow
@app.route('/connect')
def connect():
    url = stripe.OAuth.authorize_url(
        client_id=CLIENT_ID,
        scope='read_write'
    )
    return redirect(url)


# OAuth callback after the user authorizes
@app.route('/oauth/callback')
def oauth_callback():
    code = request.args.get('code')

    # Exchange authorization code for an access token
    response = stripe.OAuth.token(
        grant_type='authorization_code',
        code=code,
    )

    stripe_account_id = response['stripe_user_id']

    # Save the Stripe account ID into your database, associated with the Discord server
    discord_server_id = "some_discord_server_id"  # Replace this with actual Discord server ID

    connection = sqlite3.connect('subscriptions.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO servers (discord_server_id, stripe_account_id) VALUES (?, ?)',
                   (discord_server_id, stripe_account_id))
    connection.commit()
    connection.close()

    return f'Success! Connected Stripe account: {stripe_account_id}'


if __name__ == "__main__":
    app.run(debug=True)
