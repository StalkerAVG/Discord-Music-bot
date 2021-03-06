import discord
from discord.ext import commands
import youtube_dl
import asyncio
import re

class music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.playing = False
        self.is_paused = False

        self.queue = {}
        self.setup()
        self.ffmpeg_options = {
            'options': '-vn',
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        }
        self.ydl_opts = {'format': "bestaudio",
            'cookiefile': 'youtube.com_cookies.txt',#to access age-restricted videos on youtube, you must provide a file with cookies
            'quiet': True,
            'extract_flat': True,
            'skip_download': True}

    def setup(self):
        for guild in self.bot.guilds:
            self.queue[guild.id] = {'urls':[],'titles':[]}

    @commands.command()
    async def join(self, ctx):

        if ctx.author.voice is None:
            await ctx.send('SuS!! U r not in voice channel.')

        voice_channel = ctx.author.voice.channel

        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)

    @commands.command()
    async def leave(self,ctx):

        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
            await ctx.send('I am not in voice channel.')

    async def check_queue(self, ctx):

        if len(self.queue[ctx.guild.id]['urls']) > 0:
            await self.play_song(ctx, self.queue[ctx.guild.id]['urls'][0])
            self.queue[ctx.guild.id]['urls'].pop(0)

        else:
            ctx.voice_client.stop()
            await ctx.send('My job is done')

    async def search_song(self, amount, url, get_url=False):

        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL({'format': "bestaudio",
            'cookiefile': 'youtube.com_cookies.txt'}).extract_info(f'ytsearch{amount}:{url}', download = False, ie_key="YoutubeSearch"))

        if len(info['entries']) == 0: return None

        return 'https://www.youtube.com/watch?v='+info['entries'][0].get('id')

    async def get_link(self, ctx, song):
        url = youtube_dl.YoutubeDL(self.ydl_opts).extract_info(song, download=False)

        if 'entries' in url: #checking whether it`s playlist or not

            for i in url['entries']:#if playlist

                title = i.get('title')
                url = i.get('url')
                self.queue[ctx.guild.id]['urls'].append("https://www.youtube.com/watch?v="+url)
                self.queue[ctx.guild.id]['titles'].append(title)


        else:#if not playlist

            title, url = url.get('title'), url['formats'][0]['url']
            self.queue[ctx.guild.id]['urls'].append(url)
            self.queue[ctx.guild.id]['titles'].append(title)

    async def play_song(self, ctx, url):

        url = youtube_dl.YoutubeDL({'format': "bestaudio",
            'cookiefile': 'youtube.com_cookies.txt'}).extract_info(url, download=False)

        source_url = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(executable=r"E:\ffmpeg\bin\ffmpeg.exe", source = url['formats'][0]['url'], **self.ffmpeg_options))
        ctx.voice_client.play(source_url, after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 0.5

        title = self.queue[ctx.guild.id]['titles'].pop(0)

        await ctx.send(f'Now playing: {title}')

    @commands.command()
    async def play(self, ctx, *, song=None):

        if song is None:
            return await ctx.send('You must include a song to play')

        if ctx.voice_client is None:
            return await ctx.author.voice.channel.connect()

        if not re.search('youtube.com/watch?|https://youtube/|https//music.youtube.com/watch?', song):

            await ctx.send('Searching for a song, it will probably take a few seconds')

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send("Sorry, I could not find the given song")

            song = result

        if ctx.voice_client.source is not None:
            queue_len = len(self.queue[ctx.guild.id]['urls'])

            if queue_len < 20:
                await self.get_link(ctx, song)
                return await ctx.send(f"I am currently playing a song, this song has been added to the queue at position: {queue_len + 1}.")

            else:
                return await ctx.send("Sorry,I can only queue up to 20 songs, please wait for the current song to finish. ")

        else:
            await self.get_link(ctx, song)

            await self.play_song(ctx, self.queue[ctx.guild.id]['urls'][0])
            self.queue[ctx.guild.id]['urls'].pop(0)

    @commands.command()
    async def playlist(self, ctx, songs):

        if songs is None:
            return await ctx.send('You must include an url for playlist to play')

        if ctx.voice_client is None:
            return await ctx.author.voice.channel.connect()

        if ctx.voice_client.source is None:

            await ctx.send('Forming playlist, It`ll probably take some time')
            await self.get_link(ctx, songs)

            await self.play_song(ctx, self.queue[ctx.guild.id]['urls'][0])
            self.queue[ctx.guild.id]['urls'].pop(0)

        else:
            await ctx.send('I can`t form playlist when I play the song')

    @commands.command()
    async def queue(self, ctx):

        if len(self.queue[ctx.guild.id]['urls']) == 0:
            return await ctx.send("There are currently no songs in the queue")

        embed = discord.Embed(title='Song Queue', description = "", colour=discord.Colour.dark_blue())
        i = 1
        for title in self.queue[ctx.guild.id]['titles']:
                embed.description += f"{i}) {title}\n"
                i += 1

        embed.set_footer(text="Thanks for using me!(?????????????)????")
        await ctx.send(embed=embed)

    @commands.command()
    async def pause(self, ctx):
        await ctx.voice_client.pause()

    @commands.command()
    async def resume(self, ctx):
        await ctx.voice_client.resume()

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I am not playing any song.")

        if ctx.author.voice is None:
            return await ctx.send("You are not connected to any voice channel.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("I am not currently playing any songs for you.")

        poll = discord.Embed(title=f"Vote to Skip Song by - {ctx.author.name}#{ctx.author.discriminator}",
                             description="**80% of the voice channel must vote to skip for it to pass.**",
                             colour=discord.Colour.blue())
        poll.add_field(name="Skip", value=":white_check_mark:")
        poll.add_field(name="Stay", value=":no_entry_sign:")
        poll.set_footer(text="Voting ends in 7 seconds.")

        poll_msg = await ctx.send(
            embed=poll)  # only returns temporary message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705")  # yes
        await poll_msg.add_reaction(u"\U0001F6AB")  # no

        await asyncio.sleep(7)  # 15 seconds to vote

        poll_msg = await ctx.channel.fetch_message(poll_id)

        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1

                        reacted.append(user.id)

        skip = False

        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (
                    votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.79:  # 80% or higher
                skip = True
                embed = discord.Embed(title="Skip Successful",
                                      description="***Voting to skip the current song was succesful, skipping now.***",
                                      colour=discord.Colour.green())

        if not skip:
            embed = discord.Embed(title="Skip Failed",
                                  description="*Voting to skip the current song has failed.*\n\n**Voting failed, the vote requires at least 80% of the members to skip.**",
                                  colour=discord.Colour.red())

        embed.set_footer(text="Voting has ended.")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

        if skip:
            ctx.voice_client.stop()

def setup(client):
    client.add_cog(music(client))

