
# Discord Stripe Bot Integration

This project integrates a **Discord bot** with **Stripe** using **Flask** and **discord.py** to manage subscription systems in Discord servers. The bot listens to Stripe webhooks to assign or remove roles based on successful payments or subscription cancellations.

## Features

- **Stripe Webhook Integration**: Listens to Stripe events like `invoice.payment_succeeded` and `customer.subscription.deleted`.
- **Automatic Role Assignment**: Assigns a specific role to users in a Discord server when they successfully subscribe.
- **Automatic Role Removal**: Removes a role from users when their subscription is canceled.
- **Parallel Flask and Discord Bot Execution**: Runs both the Flask server (for Stripe webhooks) and Discord bot concurrently.

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Commands](#commands)
- [Stripe Webhook Setup](#stripe-webhook-setup)
- [Contributing](#contributing)
- [License](#license)

## Requirements

- Python 3.8+
- [Stripe account](https://stripe.com/)
- [Discord account](https://discord.com/)
- Ngrok (for local development)

### Python Packages

- `flask`
- `discord.py`
- `stripe`

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/discord-stripe-bot.git
   cd discord-stripe-bot
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows, use `venv\Scripts\activate`
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Ngrok (for local Stripe webhooks)**:
   Download Ngrok from [ngrok.com](https://ngrok.com/) and start it to forward your local Flask server:
   ```bash
   ngrok http 5000
   ```

## Configuration

1. **Create a `.env` file** in the project root with the following environment variables:
   ```plaintext
   DISCORD_TOKEN=your-discord-bot-token
   STRIPE_SECRET_KEY=your-stripe-secret-key
   STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
   FLASK_SECRET_KEY=your-flask-secret-key
   ```

2. **Get Discord Bot Token**:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications).
   - Create a new application, add a bot, and copy the token.

3. **Get Stripe API Keys**:
   - Sign in to your [Stripe Dashboard](https://dashboard.stripe.com/apikeys) and get your API keys.
   - Generate a Webhook Secret in the Dashboard under **Developers > Webhooks**.

## Usage

1. **Start the Flask and Discord Bot**:
   ```bash
   python bot.py
   ```

2. **Ngrok** will give you a public URL. Use this to configure your Stripe webhooks in the Stripe Dashboard.

3. **Stripe Webhooks**: Once a successful payment or subscription cancellation occurs, Stripe will send events to the webhook URL, and the bot will assign/remove roles in the Discord server accordingly.

## Commands

- **Slash Command**: `/connect_stripe`
   - Starts the process of connecting the Stripe account to the Discord server.
   - Provides a link to initiate Stripe OAuth flow.

## Stripe Webhook Setup

1. **Go to the Stripe Dashboard** > **Developers > Webhooks**.
2. **Add Endpoint** with the following:
   - **URL**: Your Ngrok URL (e.g., `https://xxxx.ngrok.io/stripe/webhook`)
   - **Events to Listen To**: `invoice.payment_succeeded`, `customer.subscription.deleted`
3. Copy the **Webhook Signing Secret** and add it to your `.env` file as `STRIPE_WEBHOOK_SECRET`.

## Contributing

Feel free to submit pull requests or open issues to improve the project. All contributions are welcome!

## License

This project is licensed under the MIT License.
