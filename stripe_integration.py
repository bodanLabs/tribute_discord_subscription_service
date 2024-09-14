import stripe
import os
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Create a new test customer
customer = stripe.Customer.create(
    email='testuser@example.com',
    name='Test User',
)

print(f'Customer created: {customer.id}')
