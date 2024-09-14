import sqlite3

DB_PATH = 'subscriptions.db'  # Path to the SQLite database

def get_db_connection():
    """ Get a connection to the SQLite database """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row  # Allows dictionary-like access to rows
    return connection

def create_tables():
    """ Create the necessary tables if they don't exist """
    connection = get_db_connection()
    cursor = connection.cursor()

    # Create table to store server ID and Stripe Account ID with UNIQUE constraint on discord_server_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_server_id TEXT UNIQUE NOT NULL,
            stripe_account_id TEXT NOT NULL
        )
    ''')

    # Create table to store plans and price IDs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_server_id TEXT NOT NULL,
            plan_name TEXT NOT NULL,
            price_id TEXT NOT NULL
        )
    ''')
    connection.commit()
    connection.close()



def save_stripe_account(discord_server_id, stripe_account_id):
    """ Insert or update the Stripe account ID for a Discord server """
    connection = get_db_connection()
    cursor = connection.cursor()

    # Use INSERT OR REPLACE to update if the discord_server_id already exists
    cursor.execute('''
        INSERT OR REPLACE INTO servers (discord_server_id, stripe_account_id)
        VALUES (?, ?)
    ''', (discord_server_id, stripe_account_id))

    connection.commit()
    connection.close()


def get_stripe_account(discord_server_id):
    """Retrieve the Stripe account ID for a given Discord server ID."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('''
        SELECT stripe_account_id FROM servers WHERE discord_server_id = ?
    ''', (discord_server_id,))
    result = cursor.fetchone()
    connection.close()

    if result:
        return result['stripe_account_id']
    return None


def save_plan(discord_server_id, plan_name, price_id):
    """Save the plan name and corresponding price_id to the database."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('''
        INSERT INTO plans (discord_server_id, plan_name, price_id)
        VALUES (?, ?, ?)
    ''', (discord_server_id, plan_name, price_id))
    connection.commit()
    connection.close()



def get_price_id(discord_server_id, plan_name):
    """Retrieve the price_id for a given plan name and server."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('''
        SELECT price_id FROM plans WHERE discord_server_id = ? AND plan_name = ?
    ''', (discord_server_id, plan_name))
    result = cursor.fetchone()
    connection.close()

    if result:
        return result['price_id']
    return None