# Ronin Wallet Tracker

This Python script monitors a specific Ronin wallet for incoming ERC-20 token transfers and sends a notification to a Discord channel when a new transaction is detected. The script uses the [Moralis API](https://moralis.io/) to fetch the latest transactions and the [Discord Webhook API](https://discord.com/developers/docs/resources/webhook) to send the notifications.

## Features

- Monitors a specified Ronin wallet for incoming ERC-20 token transfers.
- Sends a Discord notification when a new transaction is detected.
- Includes detailed information about the transaction in the notification:
  - Token symbol
  - Transaction hash
  - Sender address
  - Amount received

## Purpose

The Ronin Mobile Wallet application only supports notifications for a single address. In my case, I needed to monitor an additional address that the app refuses to send notifications for. This script has been designed to provide notifications for that address, with the potential for the developer to modify it to track more than one address.

## Requirements

- Python 3.7 or higher
- Required Python packages:
  - `aiohttp`
  - `discord-webhook`
  - `python-dotenv`

You can install the required packages by running:

```bash
pip install -r requirements.txt
```

## Setup

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/komiwalnut/ronin-wallet-tracker.git
   cd ronin-wallet-tracker
   ```

2. Create a .env file in the project root and add the following variables:

    ```bash
    MORALIS=moralis_api_key
    WEBHOOK=discord_webhook_url
    ADDRESS=ronin_wallet_address
    ```

3. Run the script

    ```bash
    python main.py
    ```
