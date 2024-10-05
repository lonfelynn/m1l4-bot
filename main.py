import discord
from discord.ext import commands
import random
import asyncio
import youtube_dl

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='Han, ', intents=intents)

import discord
from discord.ext import commands
import asyncio
import youtube_dl

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
    

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a file from the local filesystem"""

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing: {query}')

    @commands.command()
    async def yt(self, ctx, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing: {player.title}')

    @commands.command()
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing: {player.title}')

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @play.before_invoke
    @yt.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('hello there!')
    bot.add_cog(Music(bot))


@bot.command()
async def introduction(ctx):
    await ctx.send("My name is Han and I'm a bot on this server. I was created by Alisa. If you want to chat with me or need help, I am always here for you!")


@bot.command()
async def weather(ctx):
    await ctx.send("Well, there's no real weather in my virtual world, but I hope it's a fine sunny day in yours!")


@bot.command()
async def password(ctx, pass_length: int):
    try:
        elements = "QWERTZUIOPÜASDFGHJKLÖÄÜYXCVBNMqwertzuiopüasdfghjklöäüyxcvbnm+-/*!&$#?=@<>"
        password = ""
        for i in range(pass_length):
            password += random.choice(elements)
        await ctx.send(password)
    except Exception:
        await ctx.send('Format should include the length of a password in the end!')
        return


@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)


@bot.command()
async def hello(ctx):
    await ctx.send("Hi! How are you?")


@bot.command()
async def coin(ctx):
    flip = random.randint(0, 2)
    if flip == 0:
        await ctx.send(f"I fliped a coin, it's heads")
    else:
        await ctx.send(f"I fliped a coin, it's tails")


@bot.command()
async def repeat(ctx, times: int, content='repeating...'):
    """Repeats a message multiple times."""
    for i in range(times):
        await ctx.send(content)


@bot.command()
async def joined(ctx, member: discord.Member):
    await ctx.send(f'{member.name} joined {discord.utils.format_dt(member.joined_at)}')


@bot.group()
async def cool(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f'No, {ctx.subcommand_passed} is not cool')


@cool.command(name='Han')
async def _bot(ctx):
    """Is the bot cool?"""
    await ctx.send('Yes, Han is cool.')


@bot.command()
async def how_are_you(ctx):
    await ctx.send("I'm great! How are you?")


@bot.command()
async def bye(ctx):
    await ctx.send("bye, see you next time!")


@bot.command()
async def roll(ctx, dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)


@bot.command()
async def rock_paper_scissors(ctx, role: str):
    choices = ["rock", "paper", "scissors"]

    bot_choice = random.choice(choices)

    if role == bot_choice:
        await ctx.send(f"I chose {bot_choice}. It's a tie!")
    elif (role == "rock" and bot_choice == "scissors") or (role == "paper" and bot_choice == "rock") or (role == "scissors" and bot_choice == "paper"):
        await ctx.send(f"I chose {bot_choice}. You win, congratulations!")
    else:
        await ctx.send(f"I chose {bot_choice}. I win, hahaha!")
    

@bot.command()
async def emoji(ctx):
    emoji = ["\U0001f600", "\U0001f642", "\U0001F606", "\U0001F923", "\U0001F97A", "\U0001F9D0", "\U0001F913", "\U0001F921", "\U0001F47A", "\U0001F913", "\U0001F479", "\U0001F642", "\U0001F90C", "\U0001F60A", "\U00002620"]
    await ctx.send(random.choice(emoji))


@bot.command()
async def choose(ctx, *choices: str):
    """Chooses between multiple choices."""
    await ctx.send(random.choice(choices))






bot.run("token")
