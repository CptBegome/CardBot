

import discord
from discord.ext import commands
import re
import requests

API_URL = "https://api.pokemontcg.io/v2/cards"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def hello(ctx):
    await ctx.send("Hello! I am alive.")


def build_headers():
    return {
        "User-Agent": "Mozilla/5.0"
    }


def parse_card_input(query):
    text = query.strip()

    match = re.search(r"^(.*?)(\d+)\s*/\s*(\d+)$", text)

    if match:
        raw_name = match.group(1).strip()
        number = match.group(2)
        printed_total = match.group(3)

        raw_name = re.sub(r"([A-Za-z])(\d)$", r"\1", raw_name).strip()

        return {
            "name": raw_name,
            "number": number,
            "printed_total": printed_total
        }

    return {
        "name": text,
        "number": None,
        "printed_total": None
    }


def search_cards(query):
    parsed = parse_card_input(query)

    if parsed["number"] and parsed["printed_total"]:
        api_query = (
            f'name:"{parsed["name"]}" '
            f'number:{parsed["number"]} '
            f'set.printedTotal:{parsed["printed_total"]}'
        )
    else:
        api_query = f'name:"{parsed["name"]}"'

    params = {
        "q": api_query,
        "pageSize": 10,
        "orderBy": "name,number"
    }

    response = requests.get(
        API_URL,
        params=params,
        headers=build_headers(),
        timeout=10
    )
    response.raise_for_status()

    data = response.json()
    return data["data"]


def get_best_price(card):
    tcgplayer_prices = card.get("tcgplayer", {}).get("prices", {})

    for price_type in [
        "normal",
        "holofoil",
        "reverseHolofoil",
        "1stEditionHolofoil",
        "1stEditionNormal"
    ]:
        if price_type in tcgplayer_prices:
            market_price = tcgplayer_prices[price_type].get("market")
            if market_price is not None:
                return f"{price_type} market price: ${market_price}"

    cardmarket_prices = card.get("cardmarket", {}).get("prices", {})
    trend_price = cardmarket_prices.get("trendPrice")

    if trend_price is not None:
        return f"Cardmarket trend price: €{trend_price}"

    return "No price found."


@bot.command()
async def search(ctx, *, query):
    try:
        cards = search_cards(query)
    except requests.exceptions.RequestException as e:
        await ctx.send(f"API error: {e}")
        return

    if not cards:
        await ctx.send("No cards found.")
        return

    chosen_card = cards[0]  # for now: first result only

    name = chosen_card.get("name", "Unknown")
    set_name = chosen_card.get("set", {}).get("name", "Unknown Set")
    number = chosen_card.get("number", "?")
    printed_total = chosen_card.get("set", {}).get("printedTotal", "?")
    rarity = chosen_card.get("rarity", "No rarity")
    price = get_best_price(chosen_card)
    image_url = chosen_card.get("images", {}).get("small")

    embed = discord.Embed(
        title="🎴 Card Search",
        color=discord.Color.purple()
    )

    embed.add_field(name="Name", value=name, inline=False)
    embed.add_field(name="Set", value=set_name, inline=False)
    embed.add_field(name="Number", value=f"{number}/{printed_total}", inline=False)
    embed.add_field(name="Rarity", value=rarity, inline=False)
    embed.add_field(name="Price", value=price, inline=False)

    if image_url:
        embed.set_thumbnail(url=image_url)

    await ctx.send(embed=embed)


    
    



import os
bot.run(os.getenv("DISCORD_TOKEN"))