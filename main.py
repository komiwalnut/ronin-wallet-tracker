import os
import json
from dotenv import load_dotenv
import asyncio
import aiohttp
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime, timezone, timedelta

load_dotenv()
MORALIS_API_KEY = os.getenv("MORALIS")
DISCORD_WEBHOOK_URL = os.getenv("WEBHOOK")
RONIN_WALLET_ADDRESS = os.getenv("ADDRESS").lower()

CACHE_DIR = "./data"
CACHE_FILE = os.path.join(CACHE_DIR, "transactions.json")
QUEST_CACHE_FILE = os.path.join(CACHE_DIR, "quests.json")
MAX_CACHE_SIZE = 100

QUEST_API_URL = "https://wallet-manager.skymavis.com/quest-center/public/quests?p=1&ps=10"


def ensure_cache_file():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    if not os.path.isfile(CACHE_FILE):
        with open(CACHE_FILE, "w") as f:
            json.dump([], f)
    if not os.path.isfile(QUEST_CACHE_FILE):
        with open(QUEST_CACHE_FILE, "w") as f:
            json.dump({"last_checked": None, "known_quests": []}, f)


def load_cached_tx_hashes():
    ensure_cache_file()
    with open(CACHE_FILE, "r") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []
        except json.JSONDecodeError:
            return []


def save_cached_tx_hashes(tx_hashes):
    if len(tx_hashes) > MAX_CACHE_SIZE:
        tx_hashes = tx_hashes[-MAX_CACHE_SIZE:]
    with open(CACHE_FILE, "w") as f:
        json.dump(tx_hashes, f, indent=4)


def load_quest_cache():
    ensure_cache_file()
    with open(QUEST_CACHE_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"last_checked": None, "known_quests": []}


def save_quest_cache(cache_data):
    with open(QUEST_CACHE_FILE, "w") as f:
        json.dump(cache_data, f, indent=4)


def format_timestamp(timestamp):
    dt_object = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return dt_object.strftime("%B %d, %Y %I:%M:%S %p UTC")


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


async def fetch_available_quests():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(QUEST_API_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("code") == 200:
                        return data.get("result", {}).get("items", [])
                    else:
                        print(f"Quest API returned non-200 code: {data}")
                        return []
                else:
                    print(f"Error fetching quests: {response.status}")
                    return []
        except Exception as e:
            print(f"Exception fetching quests: {str(e)}")
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
    value_decimal = float(value_decimal)
    amount_formatted = int(value_decimal) if value_decimal.is_integer() else f"{value_decimal:.4f}"

    embed_title = f"{'Received' if incoming else 'Transferred'} Token: {token_symbol}"
    embed_color = 0x00FF00 if incoming else 0xFF0000

    embed = DiscordEmbed(title=embed_title, color=embed_color)
    embed.add_embed_field(name="Tx Hash", value=f"[View on Explorer]({tx_link})", inline=False)
    embed.add_embed_field(name="Received at", value=readable_timestamp, inline=False)
    embed.add_embed_field(name=f"{'From' if incoming else 'To'}", value=address, inline=False)
    embed.add_embed_field(name="Amount", value=amount_formatted, inline=True)
    embed.add_embed_field(name="Verified", value=verified_status, inline=True)
    embed.set_timestamp(datetime.now(timezone.utc))
    embed.set_footer(text="Disclaimer: Transactions with ❌ involves unverified contracts. Exercise caution.")

    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
    webhook.add_embed(embed)

    async with aiohttp.ClientSession() as session:
        async with session.post(DISCORD_WEBHOOK_URL, json=webhook.json):
            pass


async def send_quest_notification(quest):
    embed = DiscordEmbed(
        title=f"New Quest: {quest['name']}",
        description=quest.get('description', 'No description available'),
        color=0x1E90FF
    )

    if quest.get('logo_url'):
        embed.set_thumbnail(url=quest['logo_url'])

    end_time = quest.get('end_time')
    if end_time:
        discord_timestamp = f"<t:{end_time}:R>"
        embed.add_embed_field(name="Ends", value=discord_timestamp, inline=True)

    rewards = quest.get('rewards', [])
    if rewards:
        for reward in rewards:
            amount = reward.get('amount', 'Unknown')
            symbol = reward.get('symbol', 'Unknown')
            reward_text = f"{amount} {symbol}"
            embed.add_embed_field(name="Reward", value=reward_text, inline=True)

    if quest.get('sponsor_name'):
        embed.add_embed_field(name="Sponsor", value=quest['sponsor_name'], inline=True)

    embed.set_timestamp(datetime.now(timezone.utc))
    embed.set_footer(text="Ronin Quest Center")

    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
    webhook.add_embed(embed)

    async with aiohttp.ClientSession() as session:
        async with session.post(DISCORD_WEBHOOK_URL, json=webhook.json):
            pass


async def check_for_new_quests():
    quest_cache = load_quest_cache()
    current_time = datetime.now(timezone.utc)

    last_checked = quest_cache.get("last_checked")
    if last_checked:
        last_checked_time = datetime.fromisoformat(last_checked)
        if current_time - last_checked_time < timedelta(hours=24):
            return

    print(f"Checking for new quests at {current_time}")

    available_quests = await fetch_available_quests()
    known_quest_ids = quest_cache.get("known_quests", [])

    for quest in available_quests:
        quest_id = quest.get("id")
        if quest_id and quest_id not in known_quest_ids:
            print(f"Found new quest: {quest.get('name')}")
            await send_quest_notification(quest)
            known_quest_ids.append(quest_id)

    quest_cache["last_checked"] = current_time.isoformat()
    quest_cache["known_quests"] = known_quest_ids
    save_quest_cache(quest_cache)


async def monitor_wallet():
    while True:
        cached_tx_hashes = load_cached_tx_hashes()
        transactions = await fetch_latest_transactions()
        new_transactions = [tx for tx in transactions if tx["transaction_hash"] not in cached_tx_hashes]

        new_transactions_sorted = sorted(new_transactions, key=lambda tx: tx["block_timestamp"])

        for transaction in new_transactions_sorted:
            incoming = transaction["to_address"].lower() == RONIN_WALLET_ADDRESS
            await send_discord_notification(transaction, incoming)
            cached_tx_hashes.append(transaction["transaction_hash"])

        save_cached_tx_hashes(cached_tx_hashes)
        await asyncio.sleep(108)


async def quest_monitor():
    while True:
        try:
            await check_for_new_quests()
        except Exception as e:
            print(f"Error in quest monitor: {str(e)}")

        await asyncio.sleep(86400)


async def main():
    print("Starting Ronin Wallet Tracker with Quest Monitoring...")

    tasks = [
        asyncio.create_task(monitor_wallet()),
        asyncio.create_task(quest_monitor())
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
