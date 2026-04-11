a very gay bot
=
made by an undeniably very gay person

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

made in python 3.14 hence why there's some seemingly weird oddities in the code bc py-cord is typically used with python 3.9 but i forgot to set my python version to that when starting the project so i just opted in for shitty workarounds instead >~<

commands
-
`/yuri` - sends a random yuri image from the cache  
`/affirmation` - tells you you're a good girl

setup
-
if you just want to use the bot, refer to the link above  
else:  
1. clone the repo
2. create a .env file with `TOKEN=your_discord_token`
3. install dependencies  
   `pip install aiohttp python-dotenv py-cord audioop-lts`  
   audioop-lts isn't used by the program but py-cord throws a fit if it's not installed. it's probably my fault but i cant be bothered to do anything about it :3
4. run the bot  
   `python main.py`