# Ronin Wallet Tracker

This Python script monitors a specific Ronin wallet for incoming ERC-20 token transfers and sends a notification to a Discord channel when a new transaction is detected. The script uses the [Moralis API](https://moralis.io/) to fetch the latest transactions and the [Discord Webhook API](https://discord.com/developers/docs/resources/webhook) to send the notifications.

## Features

- Monitors a specified Ronin wallet for both incoming and outgoing ERC-20 token transfers.
- Sends a Discord notification when new transactions are detected.
- Notifications include detailed transaction information:
  - Token symbol
  - Transaction hash
  - Sender or recipient address
  - Amount transferred (formatted with commas and up to 3 decimal places)
  - Contract verification status (verified ✅ or unverified ❌)
- Tracks up to the last 20 transactions to detect new activity.

<img src="images/sample.png" alt="Received Token"/>
<img src="images/sample2.png" alt="Transferred Token"/>
<img src="images/sample3.png" alt="Old Version of Received Token"/>


### How It Works

This script checks the specified Ronin wallet for new transactions at an interval of 108 seconds. The interval is chosen to ensure efficient usage of Moralis's free-tier API limits:

- **Moralis Free Tier**: Users are allocated 40,000 Compute Units (CU) daily.
- **API Cost**: Each `erc20/transfers` call consumes 50 CU.
- **Calculation**:  
  - Daily API requests allowed: 40,000 / 50 = 800 requests/day.
  - Time between requests to stay within the limit: (24 * 60 * 60) / 800 = approx. 108 seconds.

By setting the interval to 108 seconds, the script ensures that API calls stay within the free-tier allowance, even when running continuously.

## Purpose

The Ronin Mobile Wallet application only supports notifications for a single address (weird and already reported). In my case, I needed to monitor an additional address to check if my wallet has received any airdrops, especially with the recent release of Tama.Meme, as the app refuses to send notifications for other addresses.

This script is designed to track a single wallet efficiently. If you need to monitor multiple wallets, be aware that each additional wallet increases the number of API calls. To stay within the free-tier limit, you must either:

1. **Adjust the interval**: Increase the interval between checks proportionally to account for the additional calls.
2. **Use another API key**: Obtain an additional Moralis API key to distribute the load.

For example, tracking two wallets would require doubling the interval to approximately 216 seconds, assuming the same API usage and free-tier allowance.

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

### Using a Virtual Environment (Optional)

To keep dependencies isolated, it's recommended to create a virtual environment.

1. Create a virtual environment named `rwt-venv` in the project directory:

    ```bash
    python3 -m venv rwt-venv
    ```

2. Activate the virtual environment:

    ```bash
    source rwt-venv/bin/activate
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. When done, you can deactivate the virtual environment using:

    ```bash
    deactivate
    ```

If you no longer need the virtual environment, you can remove it by deleting the `rwt-venv` folder:

```bash
rm -rf rwt-venv
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
    Note: I am running this script on a cloud server to ensure it operates continuously without interruptions. If you plan to do the same, ensure your server supports Python 3.7 or higher and has the required dependencies installed.

### PM2 Setup for Autostart

To ensure the script runs continuously and restarts automatically after server reboots, you can use **PM2**:

1. Install PM2 globally:

   ```bash
   npm install -g pm2
   ```

2. Start the script using PM2:
    
    ```bash
    pm2 start ecosystem.config.js
    ```

3. Save the PM2 process list to ensure it starts on system reboot:

   ```bash
    pm2 save
   ```

4. Configure PM2 to start on system boot:

   ```bash
    pm2 startup
   ```
