import os
from dotenv import load_dotenv
import asyncio
import aiohttp
from discord_webhook import DiscordWebhook, DiscordEmbed
from flask import Flask
from threading import Thread

load_dotenv()
MORALIS_API_KEY = os.getenv("MORALIS")
DISCORD_WEBHOOK_URL = os.getenv("WEBHOOK")
RONIN_WALLET_ADDRESS = os.getenv("ADDRESS")

app = Flask(__name__)


@app.route("/")
def home():
    return "Ronin Wallet Tracker is running!"


def run_flask():
    app.run(host="0.0.0.0", port=8080)


last_tx_hash = None


async def fetch_latest_transaction():
    url = f"https://deep-index.moralis.io/api/v2.2/{RONIN_WALLET_ADDRESS}/erc20/transfers"
    headers = {"X-API-Key": MORALIS_API_KEY}
    params = {
        "chain": "ronin",
        "order": "DESC",
        "limit": 1
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("result", [])[0] if data.get("result") else None
            else:
                print(f"Error fetching transaction: {response.status} - {await response.text()}")
                return None


async def send_discord_notification(transaction):
    global last_tx_hash
    if not transaction or transaction["transaction_hash"] == last_tx_hash:
        return

    if transaction["from_address"].lower() == RONIN_WALLET_ADDRESS:
        return

    last_tx_hash = transaction["transaction_hash"]

    token_symbol = transaction["token_symbol"]
    tx_hash = transaction["transaction_hash"]
    block_timestamp = transaction["block_timestamp"]
    from_address = transaction["from_address"]
    verified_contract = transaction["verified_contract"]
    value_decimal = transaction["value_decimal"]

    verified_status = "✅" if verified_contract else "❌"
    tx_link = f"https://app.roninchain.com/tx/{tx_hash}"

    embed = DiscordEmbed(
        title=f"Received Token: {token_symbol}",
        color=0x00FF00,
    )
    embed.add_embed_field(name="Tx Hash", value=f"[View on Explorer]({tx_link})", inline=False)
    embed.add_embed_field(name="From", value=from_address, inline=False)
    embed.add_embed_field(name="Amount", value=value_decimal, inline=True)
    embed.add_embed_field(name="Verified", value=verified_status, inline=True)
    embed.set_footer(text=f"Received at {block_timestamp} UTC")

    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
    webhook.add_embed(embed)

    async with aiohttp.ClientSession() as session:
        async with session.post(DISCORD_WEBHOOK_URL, json=webhook.json):
            pass


async def monitor_wallet():
    while True:
        transaction = await fetch_latest_transaction()
        await send_discord_notification(transaction)
        await asyncio.sleep(108)

Thread(target=run_flask).start()

asyncio.run(monitor_wallet())
