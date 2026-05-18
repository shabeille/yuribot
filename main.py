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

TAGS = ["yuri", "2girls"]
BLACKLIST = [
    "nude", "ass_focus", "sexually_suggestive", "implied_sex",
    "blood", "violence", "loli"
]

STAT_PATH = "stat.json"
AFFIRMATIONS_PATH = "affirmations.json"

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


def get_char_index_else_length(string: str, character: chr) -> int:
    if character not in string:
        return len(string)

    return string.index(character)


class YuriBotCog(discord.Cog):
    def __init__(self, bot: "YuriBot"):
        self.bot = bot
        self.refresh_yuri.change_interval(minutes=self.bot.refresh_time)
        self.refresh_yuri.start()

    @tasks.loop(minutes=1)
    async def refresh_yuri(self):
        if not self.bot.post_sent:
            return

        print("\nRefreshing yuri cache...")
        await self.bot.browser.update_cache()
        print(f"Refreshed! {await self.bot.browser.get_cache_size()} posts retrieved\n")

        self.bot.update_stat_file()
        self.bot.post_sent = False

    @discord.slash_command(
        name="affirmation",
        description=":3",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    async def affirmation(self, ctx: discord.ApplicationContext):
        await ctx.respond(choice(self.bot.affirmations))

    @discord.slash_command(
        name="yuri",
        description="get random yuri",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    @discord.option(
        "tags",
        type=discord.SlashCommandOptionType.string,
        default="",
        description="Additional tags to filter through, separated by commas (e.g. 'kissing, 2girls')"
    )
    async def yuri(self, ctx: discord.ApplicationContext, tags: str):
        tags_list: list = [] if tags == "" \
            else ([tag.strip() for tag in tags.split(',')])[:get_char_index_else_length(tags, '&')]

        try:
            response = await self.bot.browser.get_random(*tags_list)
        except IndexError:
            await ctx.respond(
                "Could not find any yuri :pensive: Make sure your tags are correct, or try again later!! :3",
                ephemeral=True
            )
            return

        image_url = response["file_url"] if self.bot.large else response["sample_url"]

        view = discord.ui.View()

        if response["source"] and response["source"] != "":
            view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.url,
                label="Original Source",
                url=response["source"]
            ))

        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.url,
            label="View on Safebooru",
            url=f"https://safebooru.org/index.php?page=post&s=view&id={response['id']}"
        ))

        embed = discord.Embed(
            title="Yuri!!!",
            description=f"Tags used: `{" ".join(tags_list)}`" if tags_list else None,
            color=discord.Colour.from_rgb(203, 166, 247)
        )
        embed.set_image(url=image_url)
        embed.set_footer(
            text=f"This is yuribot's {self.bot.total_sent}"
                 f"{choice(['st', 'nd', 'rd', 'th'])} post :3"
        )

        print(f"Sending yuri #{self.bot.total_sent}: {image_url}")

        await ctx.respond(embed=embed, view=view)
        self.bot.total_sent += 1
        self.bot.post_sent = True


class YuriBot(discord.Bot):
    def __init__(self,
         tags: list | tuple,
         cache_size: int,
         refresh_time,
         latest: bool,
         large: bool,
         stat_path, affirmations_path,
         blacklist: list | tuple = ()
        ):

        super().__init__()

        print("Initialising session...")
        self.session: None | aiohttp.ClientSession = None

        self.session = aiohttp.ClientSession()
        self.browser: SafebooruBrowser = SafebooruBrowser(
            self.session,
            default_tags= tags + [f"-{x}" for x in blacklist],
            cache_size = cache_size,
            fetch_from_latest = latest
        )

        self.large = large
        self.post_sent = True
        self.stat_path = stat_path

        with open(stat_path) as file:
            self.contents = json.loads(file.read())
            self.total_sent = self.contents["sent"]

        with open(affirmations_path) as file:
            self.affirmations: list = json.loads(file.read())

        self.refresh_time = refresh_time

        self.add_cog(YuriBotCog(self))

        try:
            from clicker import ClickerCog
            print("clicker present")
            self.add_cog(ClickerCog(self))
        except ImportError:
            print("secret module not present")

    async def on_ready(self):
        print(f"{self.user} is ready and online!")
        await self.change_presence(status=discord.Status.online)  # doesnt work for some reason

    def update_stat_file(self):
        with open(self.stat_path, "w") as file:
            self.contents["sent"] = self.total_sent
            file.write(json.dumps(self.contents))

    async def close(self):
        print("\nClosing session and updating json...")
        await self.session.close()
        self.update_stat_file()
        await super().close()



async def main():
    bot = YuriBot(
        tags=TAGS,
        cache_size=args.cache_size,
        refresh_time=args.refresh_time,
        latest=args.latest,
        large=args.large,
        stat_path=STAT_PATH,
        affirmations_path=AFFIRMATIONS_PATH,
        blacklist=BLACKLIST
    )

    while True:
        try:
            await bot.start(token)
        except aiohttp.ClientConnectorError as e:
            print(f"Network exploded :( {e}\ntrying again in 30sec...")
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            break
        else:
            break

    await bot.close()
    print("Bye bye!!! :3")

asyncio.run(main())