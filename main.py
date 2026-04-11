import os
import json
import asyncio
import aiohttp
import argparse
from time import sleep
from random import choice
from dotenv import load_dotenv

import discord
from discord.ext import tasks

from safebooru import SafebooruBrowser

STAT_PATH = "stat.json"
AFFIRMATIONS_PATH = "affirmations.json"
CLICKER_PATH = "clicker.mp3"

parser = argparse.ArgumentParser(
    prog='yuribot',
    description='discord bot to serve yuri from safebooru',
)

parser.add_argument(
    "-c", "--cache_size",
    default=1000, type=int,
    help="How many posts the bot should store in its cache"
)

parser.add_argument(
    "-r", "--refresh_time",
    default=5, type=float,
    help="How long the bot should wait (min) before refreshing its yuri cache"
)

parser.add_argument(
    "-x", "--large",
    action="store_true",
    help="When enabled, the bot will embed the full image rather than the smaller sample image"
)

parser.add_argument(
    "-l", "--latest",
    action="store_true",
    help="When enabled, this will retrieve the latest posts instead of random posts into the cache"
)

args = parser.parse_args()

print("meowing...")

load_dotenv()
token = os.getenv("TOKEN")

if token is None:
    exit("You must specify your bot token in a .env file!")

asyncio.set_event_loop(asyncio.new_event_loop()) # python3.14 shenanigans

bot = discord.Bot()
session: None | aiohttp.ClientSession = None
browser: None | SafebooruBrowser = None

with open(STAT_PATH) as file:
    contents = json.loads(file.read())
    total_sent = contents["sent"]

with open(AFFIRMATIONS_PATH) as file:
    affirmations: list = json.loads(file.read())


@bot.event
async def on_ready():
    global session, browser, total_sent # this is how you know this code sucks

    if session is None:
        print("Initialising session...")
        session = aiohttp.ClientSession()
        browser = SafebooruBrowser(
            session,
            default_tags=("yuri",),
            cache_size=args.cache_size,
            fetch_from_latest=args.latest
        )
        refresh_yuri.start()

        try:
            from clicker import register_clicker
            register_clicker(bot, session)
        except ImportError:
            print("secret module not present")

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
    }
)
async def affirmation(ctx: discord.ApplicationContext):
    await ctx.respond(choice(affirmations))


@bot.slash_command(
    name="clicker",
    description="rewawrd",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    }
)
async def clicker(ctx: discord.ApplicationContext):
    await ctx.respond(file=discord.File(CLICKER_PATH))


@bot.slash_command(
    name="yuri",
    description="get random yuri",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    }
)
async def yuri(ctx: discord.ApplicationContext):
    global total_sent
    response = await browser.get_random()

    total_sent += 1

    image_url = response["file_url"] if args.large else response["sample_url"]

    embed = discord.Embed(
        title="Yuri!!!",
        description=
        f"[[Original Source]({response["source"]})] "
        f"[[View on Safebooru](https://safebooru.org/index.php?page=post&s=view&id={response["id"]})]",
        color=discord.Colour.from_rgb(203, 166, 247)
    )
    embed.set_image(url=image_url)
    embed.set_footer(
        text=f"This is yuribot's {total_sent}"
        f"{'st' if str(total_sent)[-1] == '1'
        else 'nd' if str(total_sent)[-1] == '2'
        else 'th'} post :3"
    )

    print(f"Sending yuri #{total_sent}: {image_url}")

    await ctx.respond(embed=embed)

running = True

while running:
    try:
        bot.run(token)
    except aiohttp.ClientConnectorError as e:
        print(f"Network exploded :( {e}\ntrying again in 30sec...")
        sleep(30)
    else:
        running = False

print("\nClosing session and updating json...")

if session:
    asyncio.run(session.close())

with open(STAT_PATH, "w") as file:
    contents["sent"] = total_sent
    file.write(json.dumps(contents))

print("Bye bye!!! :3")