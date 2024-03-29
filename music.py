import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import random

class music(commands.Cog):

    def __init__(self, bot):
        
        # Variables to manage music playback and queue
        self.bot = bot
        
        self.playing = False
        self.is_paused = False
        
        self.queue = {}
        self.setup()

         # List of control emojis for music playback
        self.controls = ["⏪", "⏩", "⏯", "🔉", "🔊"]

        # FFmpeg options for audio streaming
        self.ffmpeg_options = {
            'options': '-vn',
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            'audio_codec': 'opus'
        }
        # Options for YouTube video extraction
        self.ydl_opts = {
            'format': 'bestaudio/best/m4a',
            'default_search': 'ytsearch',
            "extract_flat": "in_playlist",
        }

        
        self.bot.add_listener(self.on_reaction_add)

    def setup(self):
        for guild in self.bot.guilds:
            self.queue[guild.id] = {'urls':[],'titles':[]}

    @commands.command()
    async def leave(self,ctx):

        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
            await ctx.send('I am not in voice channel.')

    async def check_queue(self, ctx):

        if len(self.queue[ctx.guild.id]['urls']) > 0:
            
            last_url = self.queue[ctx.guild.id]['urls'].pop(0)
            last_title = self.queue[ctx.guild.id]['titles'].pop(0)
            
            self.queue[ctx.guild.id]['last_one'] = {'last_url': last_url, 'last_title': last_title}

            await self.play_song(ctx, self.queue[ctx.guild.id]['urls'][0])



        else:
            ctx.voice_client.stop()
            await ctx.send('My job is done')

    async def search_song(self, amount, url, get_url=False):

        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(self.ydl_opts).extract_info(
            f'ytsearch{amount}:{url}', download=False, ie_key="YoutubeSearch"))

        if len(info['entries']) == 0: return None

        return 'https://www.youtube.com/watch?v='+info['entries'][0].get('id')

    async def get_link(self, ctx, url, playlist):

        if playlist:

            for i in url['entries']:

                title = i.get('title')
                url = i['url']
                self.queue[ctx.guild.id]['urls'].append(url)
                self.queue[ctx.guild.id]['titles'].append(title)

            sf_pl = list(zip(self.queue[ctx.guild.id]['urls'],self.queue[ctx.guild.id]['titles']))

            random.shuffle(sf_pl)

            self.queue[ctx.guild.id]['urls'], self.queue[ctx.guild.id]['titles'] = zip(*sf_pl)
            self.queue[ctx.guild.id]['urls'], self.queue[ctx.guild.id]['titles'] = list(self.queue[ctx.guild.id]['urls']), list(self.queue[ctx.guild.id]['titles'])

        else:

            title, url = url.get('title'), url['url']
            self.queue[ctx.guild.id]['urls'].append(url)
            self.queue[ctx.guild.id]['titles'].append(title)

    async def play_song(self, ctx, url):

        if 'rr' not in url:
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                url = ydl.extract_info(url, download=False)['url']

        #redefining ffmpeg options
        ffmpeg_options = {
            'options': '-vn',
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            'executable': r"ffmpeg.exe"
        }

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(source=url, **ffmpeg_options))
        ctx.voice_client.play(source, after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 0.5

        title = self.queue[ctx.guild.id]['titles'][0]


        control_message = await ctx.send(f'Now playing: {title}')
        for control in self.controls:
            await control_message.add_reaction(control)


    @commands.command()
    async def play(self, ctx, *, song=None):
        playlist = False

        if song is None:
            return await ctx.send('You must include a song to play')

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        if song[0:4] != "http" and song[0:3] != "www":

            await ctx.send('Searching for a song, it will probably take a few seconds')

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send("Sorry, I could not find the given song")

            song = result

        url = youtube_dl.YoutubeDL(self.ydl_opts).extract_info(song, download=False)

        """'If' below is for checking whether it`s playlist or not and if it is, it will store this information for later use"""
        if 'entries' in url:
            playlist = True

        if ctx.voice_client.source is not None:
            queue_len = len(self.queue[ctx.guild.id]['urls'])

            if queue_len < 100:
                await self.get_link(ctx, url, playlist)
                if not playlist:
                    return await ctx.send(f"I am currently playing a song, this song has been added to the queue at position: {queue_len}.")
                else:
                    return await ctx.send(f"I am currently playing a song, those songs have been added to the queue.")

            else:
                return await ctx.send("Sorry,I can only queue up to 20 songs, please wait for the current song to finish. ")

        else:

            if playlist == True:
                await ctx.send('Forming playlist, It`ll probably take some time')

            await self.get_link(ctx, url, playlist)
            await self.play_song(ctx, self.queue[ctx.guild.id]['urls'][0])
            last_url = self.queue[ctx.guild.id]['urls']
            self.queue[ctx.guild.id]['las_one'] = {'last_url':last_url, 'last_title':self.queue[ctx.guild.id]['titles'][0]}


    @commands.command()
    async def queue(self, ctx):

        if len(self.queue[ctx.guild.id]['urls']) == 0:
            return await ctx.send("There are currently no songs in the queue")

        embed = discord.Embed(title='Song Queue', description = "", colour=discord.Colour.dark_blue())
        i = 0
        for title in self.queue[ctx.guild.id]['titles']:

            if not i:
                embed.description += f"Currently Playing - {title}\n"

            else:
                embed.description += f"{i}) {title}\n"

            i += 1

        embed.set_footer(text="Thanks for using me!(👉ﾟヮﾟ)👉")
        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self,ctx, *args):
        #args is the amount of songs you want to skip(it`s optional)(default=1)
        if ctx.voice_client is None:
            return await ctx.send("I am not playing any song.")

        if ctx.author.voice is None:
            return await ctx.send("You are not connected to any voice channel.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("I am not currently playing any songs for you.")

        else:
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

            await asyncio.sleep(7)  # 7 seconds to vote

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
                if len(args) == 1:
                    self.queue[ctx.guild.id]['urls'] = self.queue[ctx.guild.id]['urls'][(int(args[0])-1):]
                    self.queue[ctx.guild.id]['titles'] = self.queue[ctx.guild.id]['titles'][(int(args[0])-1):]

                ctx.voice_client.stop()

    @commands.command()
    async def stop(self, ctx):
        ctx.voice_client.stop()
        self.queue[ctx.guild.id]['urls'],self.queue[ctx.guild.id]['titles'] = [],[]

    #funtcion to automatically
    async def on_reaction_add(self, reaction, user):

        # Get the voice state of the user who added the reaction
        guild = reaction.message.guild
        guild_id = reaction.message.guild.id

        # Get the voice state of the user who added the reaction
        voice_state = guild.get_member(user.id).voice
        
        if voice_state and voice_state.channel:
            voice_client = guild.voice_client

         # Check if the reaction is a control emoji and user not bot
        if str(user) != "avg-bot#3559" and str(reaction.emoji) in self.controls:

            if str(reaction.emoji) == '🔉':
                voice_client.source.volume -= 0.1

            elif str(reaction.emoji) == '🔊':
                voice_client.source.volume += 0.1

            elif str(reaction.emoji) == "⏩":
                voice_client.stop()

            elif str(reaction.emoji) == "⏪":

                try:
                    self.queue[guild_id]['last_one']

                except NameError:
                    pass

                else:
                    self.queue[guild_id]['urls'].insert(1,self.queue[guild_id]['last_one']['last_url'])
                    self.queue[guild_id]['titles'].insert(1,self.queue[guild_id]['last_one']['last_title'])

                voice_client.stop()

            elif str(reaction.emoji) == "⏯":

                if voice_client.is_playing():
                    voice_client.pause()

                else:
                    voice_client.resume()

            # Remove the user's reaction to the control emoji
            await reaction.remove(user)

def setup(client):
    client.add_cog(music(client))

