import re

import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import ButtonStyle
import yt_dlp as youtube_dl
import asyncio
import random
import os
from dotenv import load_dotenv
load_dotenv()
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

MAX_QUEUE_LENGTH = 100
class music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.is_paused = False

        self.queue = {}
        self.setup()
        self.ydl_opts = {
            'format': 'bestaudio/best/m4a',
            'default_search': 'ytsearch',
            'extract_flat': 'in_playlist',
            'extractor_args': {
                'spotify': {
                    'search_query': 'ytsearch'  # Convert Spotify links to YouTube searches
                }
            }
        }
        self.controls = ["⏪", "⏩", "⏯", "🔉", "🔊"]
        self.bot.add_listener(self.on_reaction_add)
        self.bot.add_listener(self.on_voice_state_update)
        self.bot.add_listener(self.on_interaction)

    def setup(self):
        for guild in self.bot.guilds:
            self.queue[guild.id] = {'urls': [], 'titles': [], 'duration': [] ,'last_one': {}}

    @commands.command()
    async def leave(self, ctx):

        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
            await ctx.send('I am not in voice channel.')

    async def check_queue(self, ctx):
        """Check the queue and play the next song if there is one."""
        if len(self.queue[ctx.guild.id]['urls']) > 0:

            last_url = self.queue[ctx.guild.id]['urls'].pop(0)
            last_title = self.queue[ctx.guild.id]['titles'].pop(0)
            last_duration = self.queue[ctx.guild.id]['duration'].pop(0)

            self.queue[ctx.guild.id]['last_one'] = {'last_url': last_url, 'last_title': last_title,'last_duration': last_duration}

            try:
                await self.play_song(ctx, self.queue[ctx.guild.id]['urls'][0])
            except IndexError:
                await ctx.voice_client.stop()
                await ctx.send('There are no songs in this guild.')

        else:
            ctx.voice_client.stop()
            await ctx.send('My job is done')

    async def search_song(self, amount, url):

        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(self.ydl_opts).extract_info(
            f'ytsearch{amount}:{url}', download=False, ie_key="YoutubeSearch"))

        if len(info['entries']) == 0: return None

        for entry in info['entries']:
            if not entry.get('live_status') == 'is_live':
                return 'https://www.youtube.com/watch?v=' + entry.get('id')

        return None

    async def get_link(self, ctx, url, playlist, playlist_spotify=False):
        print("getter")

        """Get the link of the song or playlist."""
        if playlist or playlist_spotify:

            for i in url['entries']:  # if playlist
                if playlist_spotify:
                    # Spotify search results return YouTube links
                    title = i.get('title')
                    url = i.get('url')  # Extracted YouTube URL
                    duration = i.get('duration', 'None')

                else:
                    # Normal YouTube playlist
                    title = i.get('title')
                    url = i['url']
                    duration = i.get('duration', 'None')

                self.queue[ctx.guild.id]['urls'].append(url)
                self.queue[ctx.guild.id]['titles'].append(title)
                self.queue[ctx.guild.id]['duration'].append(f"{duration // 60:02d}:{duration % 60:02d}")


            sf_pl = list(zip(self.queue[ctx.guild.id]['urls'], self.queue[ctx.guild.id]['titles'],self.queue[ctx.guild.id]['duration']))

            random.shuffle(sf_pl)

            self.queue[ctx.guild.id]['urls'], self.queue[ctx.guild.id]['titles'], self.queue[ctx.guild.id]['duration'] = zip(*sf_pl)
            self.queue[ctx.guild.id]['urls'], self.queue[ctx.guild.id]['titles'], self.queue[ctx.guild.id]['duration'] = list(self.queue[ctx.guild.id]['urls']), list(self.queue[ctx.guild.id]['titles']), list(self.queue[ctx.guild.id]['duration'])
        else:  # if not playlist

            title, url, duration = url.get('title'), url['url'], url.get('duration')
            self.queue[ctx.guild.id]['urls'].append(url)
            self.queue[ctx.guild.id]['titles'].append(title)
            self.queue[ctx.guild.id]['duration'].append(f"{duration // 60:02d}:{duration % 60:02d}")


    async def play_song(self, ctx, url):
        print("playing")

        """Play the song in the voice channel."""
        if 'rr' not in url:
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:

                try:
                    url = ydl.extract_info(url, download=False)['url']
                except:
                    ctx.voice_client.stop()

        ffmpeg_options = {
            'options': '-vn',
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            'executable': r"path to ffmpeg.exe"
        }


        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(source=url, **ffmpeg_options))
        ctx.voice_client.play(source, after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 0.5

        title = self.queue[ctx.guild.id]['titles'][0]

        try:
            next_title  = self.queue[ctx.guild.id]['titles'][1]
        except IndexError:
            next_title = None

        #Embed creating

        embed = discord.Embed(
            colour=discord.Colour.dark_blue(),)

        embed.add_field(name='Now Playing',
                    value=title, inline=False,)
        embed.add_field(name='Duration',
                        value=self.queue[ctx.guild.id]['duration'][0],
                        inline=True)
        embed.add_field(name='Queue lenght',
                        value=len(self.queue[ctx.guild.id]['urls'])-1,
                        inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=True)
        embed.add_field(name='',
                        value='',
                        inline=False)
        embed.add_field(name="Previous",
                        value=self.queue[ctx.guild.id]['last_one'].get('last_title', 'None'),
                        inline=True)
        embed.add_field(name='Next',
                        value=next_title,
                        inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=True)

        view = View()

        # Add buttons to the view
        view.add_item(Button(style=ButtonStyle.grey, label='⏪', custom_id='previous'))
        view.add_item(Button(style=ButtonStyle.grey, label='⏯', custom_id='pause_play'))
        view.add_item(Button(style=ButtonStyle.grey, label='⏩', custom_id='next'))
        view.add_item(Button(style=ButtonStyle.grey, label='🔉', custom_id='volume_down'))
        view.add_item(Button(style=ButtonStyle.grey, label='🔊', custom_id='volume_up'))

        # Send the embed with the view
        control_message = await ctx.send(embed=embed, view=view)

        #for control in self.controls:
         #   await control_message.add_reaction(control)

    @commands.command()
    async def play(self, ctx, *, song=None):
        """Play a song or add it to the queue."""
        playlist = False
        playlist_spotify = False

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        if song is None:
            return await ctx.send('You must include a song to play')

        if song[0:4] != "http" and song[0:3] != "www":

            await ctx.send('Searching for a song, it will probably take a few seconds')

            result = await self.search_song(1, song)

            if result is None:
                return await ctx.send("Sorry, I could not find the given song")

            song = result

        # Check if the song is a Spotify link
        spotify_track_pattern = r"https://open.spotify.com/track/(\w+)"
        spotify_playlist_pattern = r"https://open.spotify.com/playlist/(\w+)"

        if re.match(spotify_track_pattern, song):
            track_id = re.search(spotify_track_pattern, song).group(1)
            track_info = sp.track(track_id)
            song = f"{track_info['name']} {track_info['artists'][0]['name']}"
            song = await self.search_song(1, song)

            if song is None:
                return await ctx.send("Could not find the song on YouTube.")

        elif re.match(spotify_playlist_pattern, song):
            playlist_id = re.search(spotify_playlist_pattern, song).group(1)
            playlist_info = sp.playlist_items(playlist_id)

            url = {'entries':[]}

            for track in playlist_info['items']:
                track_name = f"{track['track']['name']} {track['track']['artists'][0]['name']}"
                song_url = await self.search_song(1, track_name)

                if song_url:  # Ensure a valid result
                    video_info = youtube_dl.YoutubeDL(self.ydl_opts).extract_info(song_url, download=False)
                    url['entries'].append(video_info)

            playlist_spotify = True

            if url['entries']:
                await ctx.send(f"Adding Spotify playlist with {len(url['entries'])} tracks to the queue.")
            else:
                await ctx.send("Could not find any playable tracks from the Spotify playlist.")

        if not playlist_spotify:
            url = youtube_dl.YoutubeDL(self.ydl_opts).extract_info(song, download=False)

            """If' below is for checking whether it`s playlist or not and if it is,
             it will store this information for later use"""
            if 'entries' in url:
                playlist = True
                print("playlist")

        if ctx.voice_client.source is not None:
            queue_len = len(self.queue[ctx.guild.id]['urls'])

            if queue_len < MAX_QUEUE_LENGTH:
                await self.get_link(ctx, url, playlist, playlist_spotify)
                if not playlist or playlist_spotify:
                    return await ctx.send(f"I am currently playing a song, "
                                          f"this song has been added to the queue at position: {queue_len}.")
                else:
                    return await ctx.send("I am currently playing a song, "
                                          "those songs have been added to the queue.")

            else:
                return await ctx.send(f"Sorry,I can only queue up to {MAX_QUEUE_LENGTH} songs, "
                                      f"please wait for the current song to finish.")

        else:

            if playlist:
                await ctx.send('Forming playlist, It`ll probably take some time')

            await self.get_link(ctx, url, playlist, playlist_spotify=playlist_spotify)
            await self.play_song(ctx, self.queue[ctx.guild.id]['urls'][0])

            self.queue[ctx.guild.id]['last_one'] = {'last_url': self.queue[ctx.guild.id]['urls'], 'last_title': self.queue[ctx.guild.id]['titles'][0], 'last_duration': self.queue[ctx.guild.id]['duration'][0]}

    @commands.command()
    async def queue(self, ctx):
        """Show the current song queue."""
        if len(self.queue[ctx.guild.id]['urls']) == 0:
            return await ctx.send("There are currently no songs in the queue")

        embed = discord.Embed(title='Song Queue', description="", colour=discord.Colour.dark_blue())
        i = 0
        for title in self.queue[ctx.guild.id]['titles']:

            if not i:
                embed.description += f"currently playing - {title}\n"

            else:
                embed.description += f"{i}) {title}\n"

            i += 1

        embed.set_footer(text="Thanks for using me!(👉ﾟヮﾟ)👉")
        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx, *args):
        """
        Skip the currently playing song or multiple songs based on vote.
        If the vote to skip passes, it skips the current song and plays the next song in the queue.
        Args is the amount of songs you want to skip(it`s optional)(default=1).
        """

        # Check if the bot is playing any song
        if ctx.voice_client is None:
            return await ctx.send("I am not playing any song.")

        # Check if the user is connected to any voice channel
        if ctx.author.voice is None:
            return await ctx.send("You are not connected to any voice channel.")

        # Check if the bot is currently playing any songs for the user
        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("I am not currently playing any songs for you.")

        # Create a poll for users to vote to skip the song
        else:
            poll = discord.Embed(title=f"Vote to Skip Song by - {ctx.author.name}#{ctx.author.discriminator}",
                                 description="**80% of the voice channel must vote to skip for it to pass.**",
                                 colour=discord.Colour.blue())
            poll.add_field(name="Skip", value=":white_check_mark:")
            poll.add_field(name="Stay", value=":no_entry_sign:")
            poll.set_footer(text="Voting ends in 10 seconds.")

            poll_msg = await ctx.send(embed=poll)
            poll_id = poll_msg.id

            # Add reactions for voting
            await poll_msg.add_reaction(u"\u2705")  # yes
            await poll_msg.add_reaction(u"\U0001F6AB")  # no

            # Wait for 10 seconds for users to vote
            await asyncio.sleep(10)

            poll_msg = await ctx.channel.fetch_message(poll_id)

            votes = {u"\u2705": 0, u"\U0001F6AB": 0}
            reacted = []

            # Count the votes
            for reaction in poll_msg.reactions:
                if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                    async for user in reaction.users():
                        if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                            votes[reaction.emoji] += 1
                            reacted.append(user.id)

            skip = False

            # Check if the vote to skip has passed
            if votes[u"\u2705"] > 0:
                if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (
                        votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.79:  # 80% or higher
                    skip = True
                    embed = discord.Embed(title="Skip Successful",
                                          description="***Voting to skip the current song was successful, skipping now.***",
                                          colour=discord.Colour.green())

            # If the vote to skip has failed
            if not skip:
                embed = discord.Embed(title="Skip Failed",
                                      description="*Voting to skip the current song has failed.*\n\n**Voting failed, the vote requires at least 80% of the members to skip.**",
                                      colour=discord.Colour.red())

            embed.set_footer(text="Voting has ended.")

            await poll_msg.clear_reactions()
            await poll_msg.edit(embed=embed)

            # If the vote to skip has passed, skip the song(s)
            if skip:
                if len(args) == 1:
                    self.queue[ctx.guild.id]['urls'] = self.queue[ctx.guild.id]['urls'][(int(args[0]) - 1):]
                    self.queue[ctx.guild.id]['titles'] = self.queue[ctx.guild.id]['titles'][(int(args[0]) - 1):]

                ctx.voice_client.stop()

    @commands.command()
    async def stop(self, ctx):
        ctx.voice_client.stop()
        self.queue[ctx.guild.id]['urls'], self.queue[ctx.guild.id]['titles'] = [], []

    async def on_reaction_add(self, reaction, user):

        # Get the guild the reaction was added in
        guild = reaction.message.guild
        guild_id = reaction.message.guild.id

        # Get the voice state of the user who added the reaction
        voice_state = guild.get_member(user.id).voice
        if voice_state and voice_state.channel:
            voice_client = guild.voice_client

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
                    self.queue[guild_id]['urls'].insert(1, self.queue[guild_id]['last_one']['last_url'])
                    self.queue[guild_id]['titles'].insert(1, self.queue[guild_id]['last_one']['last_title'])
                    self.queue[guild_id]['duration'].insert(1, self.queue[guild_id]['last_one']['last_duration'])

                voice_client.stop()

            elif str(reaction.emoji) == "⏯":

                if voice_client.is_playing():
                    voice_client.pause()

                else:
                    voice_client.resume()

            await reaction.remove(user)

    async def on_interaction(self, interaction):

        # Ensure this is a button interaction
        if interaction.type == discord.InteractionType.component:

            guild = interaction.guild
            guild_id = interaction.guild_id

            # Get the voice state of the user who triggered the interaction
            voice_state = interaction.user.voice

            # Check if the user is in a voice channel
            if voice_state and voice_state.channel:
                voice_client = guild.voice_client

            if interaction.data['custom_id'] == 'pause_play':

                if voice_client.is_playing():
                    voice_client.pause()
                    await interaction.response.send_message('Paused the music.', ephemeral=True)
                elif voice_client.is_paused():
                    voice_client.resume()
                    await interaction.response.send_message('Resumed the music.', ephemeral=True)
                else:
                    await interaction.response.send_message('No music is playing right now.', ephemeral=True)
            if interaction.data['custom_id'] == 'previous':

                try:
                    self.queue[guild_id]['last_one']

                except NameError:
                    pass

                else:
                    self.queue[guild_id]['urls'].insert(1, self.queue[guild_id]['last_one']['last_url'])
                    self.queue[guild_id]['titles'].insert(1, self.queue[guild_id]['last_one']['last_title'])
                    self.queue[guild_id]['duration'].insert(1, self.queue[guild_id]['last_one']['last_duration'])

                voice_client.stop()

            if interaction.data['custom_id'] == 'next':
                voice_client.stop()

            if interaction.data['custom_id'] == 'volume_up': 
                voice_client.source.volume += 0.1
	    
            if interaction.data['custom_id'] == 'volume_down':
                voice_client.source.volume -= 0.1

            if not interaction.response.is_done():
                await interaction.response.defer()

    async def on_voice_state_update(self, member, before, after):

        """
        Event handler for voice state updates. This method is triggered when a member joins, leaves, or moves to another voice channel.
        It pauses the bot's audio in a voice channel when there is only bot in the channel, and resumes it when someone joins the channel.
        """

        # Check if the member has left a voice channel or moved to a different voice channel
        if after.channel is None or before.channel is None or after.channel.name != before.channel.name:

            # Loop over all voice clients (connections to voice channels) that the bot has
            for voice_client in self.bot.voice_clients:

                # Check if the voice client is connected to the channel the member left or the channel they joined
                if voice_client.channel == before.channel or voice_client.channel == after.channel:
                    # Get the number of members in the voice channel
                    num_mem = len(voice_client.guild.get_channel(voice_client.channel.id).members)

                    if num_mem == 1:
                        self.is_paused = True
                        await voice_client.pause()

                    elif num_mem > 1 and self.is_paused:
                        await voice_client.resume()

def setup(client):
    client.add_cog(music(client))
