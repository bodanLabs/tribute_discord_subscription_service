import json
import os
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask, session, redirect, request
import threading
from dotenv import load_dotenv
import stripe
from db_utils import create_tables, save_stripe_account, get_stripe_account, get_price_id, save_plan, \
    get_db_connection  # Import database functions
import asyncio


# Load environment variables from .env
load_dotenv()

# Stripe API key and client ID
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
CLIENT_ID = os.getenv('STRIPE_CLIENT_ID')
webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

# Intents allow your bot to listen to events like member updates
intents = discord.Intents.default()
intents.members = True

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')

# Shared in-memory storage for simplicity (use a database for production)
discord_server_ids = {}


# Initialize the Discord bot class
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!",
                         intents=intents)  # command_prefix is required but unused for slash commands

    async def setup_hook(self):
        # Sync commands to the Discord API
        guild = discord.Object(id=1239876742064246926)  # Replace with your server's guild ID for quicker syncing
        await bot.tree.sync(guild=guild)
        print(f"Slash commands synced for guild: {1239876742064246926}")

    async def on_ready(self):
        print(f'Logged in as {bot.user}')
        try:
            guild = discord.Object(id=1239876742064246926)
            await bot.tree.sync(guild=guild)  # Sync the commands for the specific guild
            print(f"Slash commands synced successfully for guild: {1239876742064246926}")
        except Exception as e:
            print(f"Error syncing commands: {e}")


# Initialize the bot object
bot = MyBot()


# Flask route for testing
@app.route('/')
def home():
    return 'Flask is running!'


# Flask route for starting OAuth
@app.route('/connect')
def connect():
    # Retrieve the discord_server_id from in-memory storage
    discord_server_id = discord_server_ids.get('discord_server_id')

    if discord_server_id is None:
        return "Error: Discord server ID is missing", 400

    # Redirect to Stripe OAuth authorization
    return redirect(
        f'https://connect.stripe.com/oauth/authorize?response_type=code&client_id={CLIENT_ID}&scope=read_write')


# **OAuth Callback Route**
@app.route('/oauth/callback')
def oauth_callback():
    # Get the authorization code from the query parameters
    code = request.args.get('code')

    if code is None:
        return "Error: No code provided", 400

    try:
        # Exchange the authorization code for an access token
        token_response = stripe.OAuth.token(
            grant_type='authorization_code',
            code=code
        )

        # Retrieve the connected Stripe account ID
        stripe_account_id = token_response['stripe_user_id']

        # Retrieve the Discord server ID from in-memory storage (or session/database)
        discord_server_id = discord_server_ids.get('discord_server_id')

        if discord_server_id is None:
            return "Error: Discord server ID is missing", 400

        # Save the stripe_account_id and discord_server_id to the database
        save_stripe_account(discord_server_id, stripe_account_id)

        return f"Success! Connected Stripe Account ID: {stripe_account_id} for Discord Server ID: {discord_server_id}"

    except stripe.error.StripeError as e:
        return f"Error exchanging code: {str(e)}", 500


# Define a slash command to trigger the Stripe OAuth flow
@bot.tree.command(name="connect_stripe")
async def connect_stripe(interaction: discord.Interaction):
    """Slash command to start the OAuth process and store the server ID."""
    discord_server_id = str(interaction.guild.id)  # Fetch the server's unique ID

    # Retrieve the Stripe account ID from the database
    stripe_account_id = get_stripe_account(discord_server_id)

    if stripe_account_id:
        await interaction.response.send_message(f"Error: A Stripe account is already connected for this server. Use `/remove_stripe_account` to remove it.", ephemeral=True)
        return

    # Store the discord_server_id in memory (replace with database for production)
    discord_server_ids['discord_server_id'] = discord_server_id

    # Provide a link for the user to initiate the OAuth flow
    await interaction.response.send_message(f"Click the link to connect Stripe: http://localhost:5000/connect")



# **New slash command to create a subscription plan**
# **Modified create_plan command**
@bot.tree.command(name="create_plan")
@app_commands.describe(plan_name="Name of the subscription plan", price="Price of the subscription in USD")
async def create_plan(interaction: discord.Interaction, plan_name: str, price: float):
    """Slash command to create a subscription plan for the server."""
    discord_server_id = str(interaction.guild.id)  # Fetch the server's unique ID

    # Retrieve the Stripe account ID from the database
    stripe_account_id = get_stripe_account(discord_server_id)

    if stripe_account_id is None:
        await interaction.response.send_message("Error: No Stripe account connected for this server.", ephemeral=True)
        return

    try:
        # Create a Stripe product (representing the plan)
        product = stripe.Product.create(
            name=plan_name,
            stripe_account=stripe_account_id
        )

        # Create a Stripe price (representing the recurring subscription)
        price_object = stripe.Price.create(
            unit_amount=int(price * 100),  # Stripe expects the amount in cents
            currency='usd',
            recurring={"interval": "month"},  # Set to monthly subscription
            product=product.id,
            stripe_account=stripe_account_id
        )

        # Save the plan and price ID to the database
        save_plan(discord_server_id, plan_name, price_object.id)

        # Respond to the user with the success message
        await interaction.response.send_message(f"Plan '{plan_name}' created with a price of ${price:.2f}/month.\nPrice ID: {price_object.id}")

    except stripe.error.StripeError as e:
        await interaction.response.send_message(f"Error creating the plan: {str(e)}", ephemeral=True)


# **New slash command to subscribe to a plan**
@bot.tree.command(name="subscribe")
@app_commands.describe(plan_name="Name of the plan to subscribe to")
async def subscribe(interaction: discord.Interaction, plan_name: str):
    """Slash command to subscribe to a specific plan."""
    discord_server_id = str(interaction.guild.id)  # Fetch the server's unique ID

    # Retrieve the Stripe account ID from the database
    stripe_account_id = get_stripe_account(discord_server_id)

    if stripe_account_id is None:
        await interaction.response.send_message("Error: No Stripe account connected for this server.", ephemeral=True)
        return

    # Retrieve the Price ID based on the plan name
    price_id = get_price_id(discord_server_id, plan_name)

    if price_id is None:
        await interaction.response.send_message(f"Error: No plan named '{plan_name}' was found.", ephemeral=True)
        return

    try:
        # Create a checkout session for the user to subscribe to the plan
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://yourdomain.com/success',
            cancel_url='https://yourdomain.com/cancel',
            client_reference_id=str(interaction.user.id),  # Save the Discord user ID as a reference
            stripe_account=stripe_account_id
        )

        # Send the checkout URL to the user
        await interaction.response.send_message(f"Click the link to subscribe: {session.url}", ephemeral=True)

    except stripe.error.StripeError as e:
        await interaction.response.send_message(f"Error creating checkout session: {str(e)}", ephemeral=True)


# **New slash command to remove the connected Stripe account**
@bot.tree.command(name="remove_stripe_account")
async def remove_stripe_account(interaction: discord.Interaction):
    """Slash command to remove the connected Stripe account for the server."""
    discord_server_id = str(interaction.guild.id)  # Fetch the server's unique ID

    # Retrieve the Stripe account ID from the database
    stripe_account_id = get_stripe_account(discord_server_id)

    if not stripe_account_id:
        await interaction.response.send_message("Error: No Stripe account is connected for this server.", ephemeral=True)
        return

    # Remove the Stripe account for this server
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM servers WHERE discord_server_id = ?', (discord_server_id,))
    connection.commit()
    connection.close()

    await interaction.response.send_message("Stripe account has been removed. You can now connect a new Stripe account.")


# Function to run Flask in a separate thread
def run_flask():
    # Create the necessary database tables
    create_tables()

    # Run Flask
    app.run(port=5000, debug=False)


def handle_payment_failure(data):
    """Handle failed payment events."""
    discord_user_id = data.get('client_reference_id')

    if discord_user_id:
        user = bot.get_user(int(discord_user_id))
        # Optionally, notify the user about the failed payment
        print(f"Payment failed for user: {user.name}.")


# Flask route to handle Stripe webhooks
@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    print("Webhook received!")
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        # Directly parse the payload without checking the signature
        event = json.loads(payload)
        print(f"Received event: {event['type']}")
    except ValueError:
        return "Invalid payload", 400

    # Process Stripe events asynchronously
    if event['type'] == 'invoice.payment_succeeded':
        print("Processing payment success...")
        bot.loop.create_task(handle_payment_success(event['data']['object']))
    elif event['type'] == 'customer.subscription.deleted':
        print("Processing subscription cancellation...")
        bot.loop.create_task(handle_subscription_cancellation(event['data']['object']))

    return "Success", 200

# Function to handle successful payments and assign roles
async def handle_payment_success(data):
    print("Handling payment success...")
    discord_user_id = data.get('client_reference_id')

    if discord_user_id:
        print(f"User ID: {discord_user_id}")
        user = bot.get_user(int(discord_user_id))
        guild = bot.get_guild(1239876742064246926)  # Replace with your guild ID
        role = guild.get_role(1281580865935114292)  # Replace with your subscriber role ID
        if user and role:
            member = guild.get_member(user.id)
            if member:
                await member.add_roles(role)
                print(f"Assigned role {role.name} to {user.name}.")
                await user.send(f"Thank you for subscribing! You've been assigned the {role.name} role in {guild.name}.")
            else:
                print(f"Member not found for user {user.name}")
        else:
            print(f"User or role not found for ID {discord_user_id}")

# Function to handle subscription cancellation and remove roles
async def handle_subscription_cancellation(data):
    print("Handling subscription cancellation...")
    discord_user_id = data.get('client_reference_id')

    if discord_user_id:
        print(f"User ID: {discord_user_id}")
        user = bot.get_user(int(discord_user_id))
        guild = bot.get_guild(1239876742064246926)  # Replace with your guild ID
        role = guild.get_role(1281580865935114292)  # Replace with your subscriber role ID
        if user and role:
            member = guild.get_member(user.id)
            if member:
                await member.remove_roles(role)
                print(f"Removed role {role.name} from {user.name}.")
                await user.send(f"Your subscription has been canceled, and the {role.name} role has been removed in {guild.name}.")
            else:
                print(f"Member not found for user {user.name}")
        else:
            print(f"User or role not found for ID {discord_user_id}")


# Run both the Flask app and the Discord bot

if __name__ == "__main__":
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Run the Discord bot (this runs on the main thread)
    bot.run(os.getenv('DISCORD_TOKEN'))
