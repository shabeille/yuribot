import io
import os
import json
import asyncio

import aiohttp
import argparse
from random import choice

from matplotlib import pyplot, rcParams
from dotenv import load_dotenv

import discord
from discord.ext import tasks

from safebooru import SafebooruBrowser
from stats_mgr import StatsManager

DEFAULT_TAGS = ["yuri", "2girls"]
DEFAULT_BLACKLIST = [
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

parser.add_argument(
    "-b", "--blacklist",
    nargs="*",
    help="Tags to add to the blacklist, separated by spaces",
    default=DEFAULT_BLACKLIST
)

parser.add_argument(
    "-d", "--default-tags",
    nargs="*",
    help="Tags to include in every query (e.g. 'yuri'), separated by spaces",
    default=DEFAULT_TAGS
)

args = parser.parse_args()

print("meowing...")

load_dotenv()
token = os.getenv("TOKEN")

if token is None:
    exit("You must specify your bot token in a .env file!")

TEXT_COLOR = '#cdd6f4'
rcParams['text.color'] = TEXT_COLOR
rcParams['axes.labelcolor'] = TEXT_COLOR
rcParams['xtick.color'] = TEXT_COLOR
rcParams['ytick.color'] = TEXT_COLOR


async def download_image(session: aiohttp.ClientSession, url) -> bytes:
    async with session.get(url) as resp:
        resp.auto_decompress = False
        return await resp.read()


class RepeatView(discord.ui.View):
    def __init__(self, cog: "YuriBotCog", tags_list):
        super().__init__()
        self.cog = cog
        self.tags_list = tags_list

    @discord.ui.button(
        label="Repeat",
        style=discord.ButtonStyle.primary
    )
    async def repeat_callback(self, button, interaction):
        await self.cog.send_yuri(interaction.followup.send, self.tags_list, interaction.response.defer)


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

        self.bot.stats.write_file()
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

    @staticmethod
    async def autocomplete_yuri(ctx: discord.AutocompleteContext):
        tag: str = ctx.options["tags"]
        cog = ctx.bot.get_cog("YuriBotCog")
        assert isinstance(cog, YuriBotCog)

        tags = tag.split(',')

        autocomplete_output = await cog.bot.browser.autocomplete(tag)
        prefix = (
            (','.join(tags[:-1]) + ',' if len(tags) > 1 else '') # for all da preceding tagz
            + ('-' if len(tags[-1]) > 0 and tags[-1][0] == '-' else '') # for da blacklisted tag. meow :3 !!
        )

        autocomplete_options = [
            prefix + option["value"]
            for option in autocomplete_output
            if option["value"] not in cog.bot.blacklist
        ]

        return autocomplete_options

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
        description="Additional tags to filter through, separated by commas (e.g. 'kissing,2girls')",
        autocomplete=discord.utils.basic_autocomplete(autocomplete_yuri)
    )
    async def yuri(self, ctx: discord.ApplicationContext, tags: str):
        index = len(tags) if '&' not in tags else tags.index('&')
        tags_list: list = (
            [] if tags == "" else (
                [tag.strip() for tag in (tags[:index]).split(',')]
        ))

        await self.send_yuri(ctx.respond, tags_list, ctx.defer)

    async def send_yuri(self, send, tags_list: list, defer):
        try:
            response = await self.bot.browser.get_random(*tags_list)
        except IndexError:
            await send(
                "Could not find any yuri :pensive: Make sure your tags are correct, or try again later!! :3",
                ephemeral=True
            )
            return

        await defer()

        image_url = response["file_url"] if self.bot.large else response["sample_url"]
        buffer: bytes = await download_image(self.bot.session, image_url)
        file = discord.File(
            io.BytesIO(buffer),
            f"yuri{os.path.splitext(image_url)[-1]}"
        )

        view = RepeatView(self, tags_list)

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
        embed.set_image(url=f"attachment://{file.filename}")
        embed.set_footer(
            text=f"This is {self.bot.user.display_name}'s {self.bot.stats.get_posts_sent() + 1}"
                 f"{choice(['st', 'nd', 'rd', 'th'])} post :3"
        )

        print(f"Sending yuri #{self.bot.stats.get_posts_sent() + 1}: {image_url}")
        await send(embed=embed, view=view, file=file)

        file.close()
        
        self.bot.stats.record_post_sent()
        if tags_list:
            for tag in set(tags_list):
                self.bot.stats.record_tag_used(tag.strip())

        self.bot.post_sent = True
    
    @discord.slash_command(
        name="tagchart",
        description="Shows a chart of the most searched for tags",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    @discord.option(
        "count",
        type=discord.SlashCommandOptionType.integer,
        default=25,
        description="number of tags to show in the chart (defaults to 25)"
    )
    async def tag_stats(self, ctx: discord.ApplicationContext, count: int):
        await ctx.defer()
        
        fix, ax = pyplot.subplots()
        keys, vals = zip(*sorted(self.bot.stats.get_tags_used().items(), key=lambda x: x[1]))

        fix.set_facecolor("#181825")
        fix.set_edgecolor("#cdd6f4")
        ax.barh(keys[-count:], vals[-count:], color='#cba6f7')
        ax.set_xlabel("Searches")
        ax.set_ylabel("Tag")
        ax.set_title(f"top {count} yuribot searches by tag")
        ax.set_facecolor("#1e1e2e")
        
        with io.BytesIO() as buffer:
            fix.savefig(buffer, format="png", bbox_inches='tight')
            buffer.seek(0)
            await ctx.respond(file=discord.File(buffer, "graph.png"))


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
        self.stats = StatsManager(stat_path)
        self.blacklist: list | tuple = blacklist

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
        act = discord.Game("watching yuri")
        await self.change_presence(status=discord.Status.online, activity=act)

    async def close(self):
        print("\nClosing session and updating json...")
        await self.session.close()
        self.stats.write_file()
        await super().close()


async def main():
    bot = YuriBot(
        tags=args.default_tags,
        cache_size=args.cache_size,
        refresh_time=args.refresh_time,
        latest=args.latest,
        large=args.large,
        stat_path=STAT_PATH,
        affirmations_path=AFFIRMATIONS_PATH,
        blacklist=args.blacklist
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
