import stripe
import os
from flask import Flask, request, redirect, session, url_for
from dotenv import load_dotenv
import sqlite3


@app.route('/webhook', methods=['POST'])
def webhook_received():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    endpoint_secret = os.getenv('STRIPE_ENDPOINT_SECRET')  # Set your Stripe webhook secret
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    # Handle different event types
    if event['type'] == 'invoice.payment_succeeded':
        # Assign role in Discord
        handle_payment_success(event['data']['object'])

    elif event['type'] == 'invoice.payment_failed':
        # Remove role in Discord
        handle_payment_failure(event['data']['object'])

    return '', 200

def handle_payment_success(invoice):
    # Get the customer ID and find the corresponding Discord user
    customer_id = invoice['customer']
    # Assign roles logic goes here
    print(f"Payment succeeded for customer {customer_id}")

def handle_payment_failure(invoice):
    customer_id = invoice['customer']
    print(f"Payment failed for customer {customer_id}")
