a very gay bot
=
made by some undeniably very gay people

here's the auth link to the one i'm hosting:  
https://discord.com/oauth2/authorize?client_id=1482579213729923112

yeah the code is a bit ugly but whatever

it works by retrieving a Lot of posts tagged with yuri from safebooru every couple minutes and then randomly choosing one every time /yuri is called

made sure to add your token in a .env file if you're hosting this yourself

<img src="https://file.garden/Z8ob9c5zoiDzLl-Q/yuriexample.png" width="400" alt="example image of /yuri command output">

dependencies
-
* aiohttp
* python-dotenv
* py-cord

commands
-
`/yuri` - sends a random yuri image from the cache  
`/affirmation` - tells you you're a good girl
`/tagchart` - shows a chart of the frequency of tags passed into `/yuri`

setup
-
if you just want to use the bot, refer to the link above  
else:  
1. clone the repo
2. create a .env file with `TOKEN=your_discord_token`
3. install dependencies  
   `pip install -r requirements.txt`
4. run the bot  
   `python main.py`

arguments
-
- `-h`: Shows a more detailed help page
- `-c <number>`: How many posts the bot should store in its cache
- `-r <number>`: How many minutes the bot should wait before refreshing the post cache
- `-x`: Whether to embed the full image rather than the smaller sample image
- `-l`: Whether to fill the cache with latest posts instead of random ones
- `-b [tag1] [tag2] [tag3] ...`: Tags to blacklist from being shown
- `-d [tag1] [tag2] [tag3] ...`: Tags to include in every request (e.g. "yuri")
