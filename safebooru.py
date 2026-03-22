from string import Template
from urllib.parse import urljoin
from random import choice, randrange
import asyncio
import xmltodict

sleep_length = 0.5

website_url: str = "https://safebooru.org/"
latest_prefix: Template = Template(
    "index.php?page=dapi&s=post&q=index&json=1"
    "&limit=${limit}"
    "&tags=${tags}"
)
random_prefix: Template = Template(
    "index.php?page=dapi&s=post&q=index&json=1&limit=1"
    "&pid=${offset}"
    "&tags=${tags}"
)

tag_prefix: Template = Template(
    "index.php?page=dapi&s=tag&q=index"
    "&name=${tag_name}"
)

class SafebooruBrowser:
    def __init__(self, session, cache_size=100, default_tags=None, get_latest=False):
        self._session = session

        if default_tags is not None and type(default_tags) not in (tuple, list, str):
            raise TypeError("Default tags must be passed in as a tuple or list, or a string containing one tag")

        self.default_tags = [] if (
                default_tags is None) else [default_tags] if (
                type(default_tags) == str) else list(default_tags)

        if len(self.default_tags) > 1 and not get_latest:
            raise NotImplementedError("Using multiple tags when fetching randomly is not yet supported")

        self.cache_size = cache_size
        self._cached_posts = []

        self.single_cache_updates = 0

        self.get_latest = get_latest

    async def _get_json_response(self, url):
        async with self._session.get(url) as resp:
            return await resp.json()

    async def refill_cache(self) -> None:
        tags = '+'.join(self.default_tags)
        url = urljoin(
            website_url,
            latest_prefix.substitute(
                limit = self.cache_size,
                tags = tags
            )
        )
        self._cached_posts = await self._get_json_response(url)

    async def update_one(self):
        random_index = randrange((await self.get_tag_count(self.default_tags[0])) // 10)
        # divided by 10 since i find that older posts are often very... subpar. They fucking suck basically.

        url = urljoin(
            website_url,
            random_prefix.substitute(
                offset=random_index,
                tags=self.default_tags[0]
            )
        )

        new_post = (await self._get_json_response(url))[0]

        if len(self._cached_posts) < self.cache_size:
            self._cached_posts.append(new_post)
        else:
            self._cached_posts[self.single_cache_updates % self.cache_size] = new_post

        self.single_cache_updates += 1


    async def get_random(self, *args):
        """
        Returns the full unpacked json of a random post currently stored in the cache
        :param args: any additional tags to limit the search to
        :return: the full unpacked json of a random post in the cache
        """
        if not self._cached_posts:
            raise RuntimeError("Cache is empty")

        return choice(self._cached_posts if len(args) == 0 else [
            post for post in self._cached_posts
            if all(tag in post["tags"].split(' ') for tag in args)
        ])

    async def get_cache_size(self):
        return len(self._cached_posts)

    async def get_tag_count(self, tag: str) -> int:
        # flawed: only works for one tag lol
        url = urljoin(
            website_url,
            tag_prefix.substitute(
                tag_name=tag
            )
        )

        async with self._session.get(url) as resp:
            tag_response = xmltodict.parse(await resp.text())
            return int(tag_response["tags"]["tag"]["@count"]) # duct tape i think
