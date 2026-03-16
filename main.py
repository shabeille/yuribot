import os
import json
import asyncio
import aiohttp
import argparse
from random import choice
from dotenv import load_dotenv

import discord
from discord.ext import tasks

from safebooru import SafebooruBrowser


parser = argparse.ArgumentParser(
    prog='yuribot',
    description='discord bot to serve yuri from safebooru',
)

print("meowing...")

load_dotenv()
token = os.getenv("TOKEN")

if token is None:
    exit("You must specify your bot token in a .env file!")

parser.add_argument(
    "-c", "--cache_size",
    default=1000, type=int,
    help="How many posts the bot should store in its cache"
)

parser.add_argument(
    "-r", "--refresh_time",
    default=10, type=float,
    help="How long the bot should wait before refreshing its yuri cache"
)

args = parser.parse_args()

asyncio.set_event_loop(asyncio.new_event_loop())

bot = discord.Bot()
session: None | aiohttp.ClientSession = None
browser: None | SafebooruBrowser = None

with open("stat.json") as file:
    contents = json.loads(file.read())
    total_sent = contents["sent"]

with open("affirmations.json") as file:
    affirmations: list = json.loads(file.read())


@bot.event
async def on_ready():
    global session, browser, total_sent # this is how you know this code sucks

    if session is None:
        session = aiohttp.ClientSession()
        browser = SafebooruBrowser(session, default_tags=("yuri",), cache_size=args.cache_size)
        refresh_yuri.start()

    print(f"{bot.user} is ready and online!")
    await bot.change_presence(status=discord.Status.online) # doesnt work for some reason


@tasks.loop(minutes=args.refresh_time)
async def refresh_yuri():
    print("\nRefreshing yuri cache...")
    await browser.update_cache()
    print(f"Refreshed! {await browser.get_cache_size()} posts retrieved\n")


@bot.slash_command(
    name="affirmation",
    description=":3",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    },
    contexts={
        discord.InteractionContextType.guild,
        discord.InteractionContextType.bot_dm,
        discord.InteractionContextType.private_channel
    }
)
async def affirmation(ctx: discord.ApplicationContext):
    await ctx.respond(choice(affirmations))


@bot.slash_command(
    name="yuri",
    description="get random yuri",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    },
    contexts={
        discord.InteractionContextType.guild,
        discord.InteractionContextType.bot_dm,
        discord.InteractionContextType.private_channel
    }
)
async def yuri(ctx: discord.ApplicationContext):
    global total_sent
    response = await browser.get_random()

    total_sent += 1

    embed = discord.Embed(
        title="Yuri!!!",
        description=f"Source: {response["source"]}",
        color=discord.Colour.from_rgb(203, 166, 247)
    )
    embed.set_image(url=response["file_url"])
    embed.set_footer(
        text=f"This is yuribot's {total_sent}"
        f"{'st' if str(total_sent)[-1] == '1'
        else 'nd' if str(total_sent)[-1] == '2'
        else 'th'} post :3"
    )

    print(f"Sending yuri #{total_sent}: {response["file_url"]}")

    await ctx.respond(embed=embed)


bot.run(token)

print("\nClosing session and updating json...")

if session:
    asyncio.run(session.close())

with open("stat.json", "w") as file:
    contents["sent"] = total_sent
    file.write(json.dumps(contents))

print("Bye bye!!! :3")