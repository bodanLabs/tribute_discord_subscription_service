import sqlite3

def create_tables():
    connection = sqlite3.connect('subscriptions.db')
    cursor = connection.cursor()

    # Create table to store user subscription info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_user_id TEXT NOT NULL,
            stripe_customer_id TEXT,
            subscription_status TEXT,
            role_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create table to store Stripe accounts for each server (for OAuth)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_server_id TEXT NOT NULL,
            stripe_account_id TEXT NOT NULL
        )
    ''')

    connection.commit()
    connection.close()

if __name__ == "__main__":
    create_tables()
