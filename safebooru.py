from string import Template
from urllib.parse import urljoin
from random import choice, randint
import xmltodict

POSTS_PER_PAGE = 42

website_url: str = "https://safebooru.org/"

post_prefix: Template = Template(
    "index.php?page=dapi&s=post&q=index&json=1"
    "&limit=${limit}"
    "&tags=${tags}"
    "&pid=${offset}"
)
tag_prefix: Template = Template(
    "index.php?page=dapi&s=tag&q=index"
    "&name=${tag_name}"
)



    

class SafebooruBrowser:
    def __init__(self, session, cache_size=1000, default_tags=None, random_offset:bool=True):
        self._session = session

        if default_tags is not None and type(default_tags) not in (tuple, list):
            raise TypeError("Default tags must be passed in as a tuple or list")

        self.default_tags = [] if default_tags is None else list(default_tags)

        self.cache_size = cache_size
        self._cached_posts = []

        self.do_offset: bool = random_offset
        self._offset: int = -1 # Set to -1 when no offset is present

    async def _get_json_response(self, url):
        async with self._session.get(url) as resp:
            return await resp.json()

    async def update_cache(self):
        tags = '+'.join(self.default_tags)

        url = urljoin(
            website_url,
            post_prefix.substitute(
                limit = self.cache_size,
                tags = tags,
                offset = 0 if self._offset == -1 else self._offset
            )
        )

        self._cached_posts = await self._get_json_response(url)

        tag_count = await self.get_tag_count(self.default_tags[0])

        if self.do_offset and tag_count >= self.cache_size:
            self._offset = randint(0, tag_count - self.cache_size)
            print(f"Offset of {self._offset}")

    async def get_random(self, *args):
        """
        Returns the full unpacked json of a random post currently stored in the cache
        :param args: any additional tags to limit the search to
        :return: the full unpacked json of a random post in the cache
        """
        return choice(self._cached_posts if len(args) == 0 else [
            post for post in self._cached_posts
            if all(tag in post["tags"].split(' ') for tag in args)
        ])

    async def get_cache_size(self):
        return len(self._cached_posts)

    async def get_tag_count(self, tag: str) -> int:
        url = urljoin(
            website_url,
            tag_prefix.substitute(
                tag_name=tag
            )
        )

        async with self._session.get(url) as resp:
            tag_response = xmltodict.parse(await resp.text())
            return int(tag_response["tags"]["tag"]["@count"]) # duct tape i think
