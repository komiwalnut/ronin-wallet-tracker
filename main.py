import os
from dotenv import load_dotenv
import asyncio
import aiohttp
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime

load_dotenv()
MORALIS_API_KEY = os.getenv("MORALIS")
DISCORD_WEBHOOK_URL = os.getenv("WEBHOOK")
RONIN_WALLET_ADDRESS = os.getenv("ADDRESS").lower()

last_tx_hashes = []


def format_timestamp(timestamp):
    dt_object = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return dt_object.strftime("%B %d, %Y %I:%M:%S %p UTC")


def format_amount(amount):
    return f"{float(amount):,.4f}"


async def fetch_latest_transactions():
    url = f"https://deep-index.moralis.io/api/v2.2/{RONIN_WALLET_ADDRESS}/erc20/transfers"
    headers = {"X-API-Key": MORALIS_API_KEY}
    params = {
        "chain": "ronin",
        "order": "DESC",
        "limit": 20
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("result", [])
            else:
                print(f"Error fetching transactions: {response.status} - {await response.text()}")
                return []


async def send_discord_notification(transaction, incoming):
    token_symbol = transaction["token_symbol"]
    tx_hash = transaction["transaction_hash"]
    block_timestamp = transaction["block_timestamp"]
    address = transaction["from_address"] if incoming else transaction["to_address"]
    verified_contract = transaction["verified_contract"]
    value_decimal = transaction["value_decimal"]

    readable_timestamp = format_timestamp(block_timestamp)
    verified_status = "✅" if verified_contract else "❌"
    tx_link = f"https://app.roninchain.com/tx/{tx_hash}"
    amount_formatted = format_amount(value_decimal)

    embed_title = f"{'Received' if incoming else 'Transferred'} Token: {token_symbol}"
    embed_color = 0x00FF00 if incoming else 0xFF0000

    embed = DiscordEmbed(title=embed_title, color=embed_color)
    embed.add_embed_field(name="Tx Hash", value=f"[View on Explorer]({tx_link})", inline=False)
    embed.add_embed_field(name="Received at", value=readable_timestamp, inline=False)
    embed.add_embed_field(name=f"{'From' if incoming else 'To'}", value=address, inline=False)
    embed.add_embed_field(name="Amount", value=amount_formatted, inline=True)
    embed.add_embed_field(name="Verified", value=verified_status, inline=True)
    embed.set_footer(text="Disclaimer: Transactions with ❌ involves unverified contracts. Exercise caution.")

    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
    webhook.add_embed(embed)

    async with aiohttp.ClientSession() as session:
        async with session.post(DISCORD_WEBHOOK_URL, json=webhook.json):
            pass


async def monitor_wallet():
    global last_tx_hashes
    while True:
        transactions = await fetch_latest_transactions()
        new_tx_hashes = [tx["transaction_hash"] for tx in transactions]

        for transaction in transactions[::-1]:
            if transaction["transaction_hash"] not in last_tx_hashes:
                incoming = transaction["to_address"].lower() == RONIN_WALLET_ADDRESS
                await send_discord_notification(transaction, incoming)

        last_tx_hashes = new_tx_hashes
        await asyncio.sleep(108)


asyncio.run(monitor_wallet())
