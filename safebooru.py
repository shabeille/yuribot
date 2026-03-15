from string import Template
from urllib.parse import urljoin
from random import choice

POSTS_PER_PAGE = 42

website_url: str = "https://safebooru.org/"
prefix: Template = Template(
    "index.php?page=dapi&s=post&q=index&json=1"
    "&limit=${limit}"
    "&tags=${tags}"
)

class SafebooruBrowser:
    def __init__(self, session, cache_size=1000, default_tags=None, remove_duplicates=True):
        self._session = session

        if default_tags is not None and type(default_tags) not in (tuple, list):
            raise TypeError("Default tags must be passed in as a tuple or list")

        self.default_tags = [] if default_tags is None else list(default_tags)

        self.cache_size = cache_size
        self._cached_posts = []

        self.remove_duplicates = remove_duplicates

    async def _get_json_response(self, url):
        async with self._session.get(url) as resp:
            return await resp.json()

    async def update_cache(self):
        tags = '+'.join(self.default_tags)

        url = urljoin(
            website_url,
            prefix.substitute(
                limit = self.cache_size,
                tags = tags
            )
        )

        self._cached_posts = await self._get_json_response(url)

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
