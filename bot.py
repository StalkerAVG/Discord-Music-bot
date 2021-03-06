import discord
from discord.ext import commands
import re
from decode import *
from defweather import *
import os, random
import time
from music import music
from botconfig import token

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix = '%', intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching,name="Як Б'ють Кацапів")
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    print("Bot is ready!")

@bot.event
async def on_message(message):

    if "Слава Україні" in message.content:
        channel = message.channel
        await channel.send('Героям Слава')

    if "Glory to Ukraine" in message.content:
        channel = message.channel
        await channel.send('Glory to Heroes')

    if re.search('%uwu|uwu|%UwU|UwU', message.content):
        """function for fun"""

        channel = message.channel
        randmsg = random.choice(os.listdir("other\photos"))
        await channel.send(file=discord.File(f"other\photos\{randmsg}"))

        channel = message.author.voice.channel
        vc = await channel.connect()
        vc.play(discord.FFmpegPCMAudio(executable=r"E:\ffmpeg\bin\ffmpeg.exe", source = r'other\sounds\Uwu.mp3'))
        time.sleep(3)
        await vc.disconnect()

    await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(payload):
    """function for translates message from the English keyboard layout to Ukrainian"""
    if payload.emoji.name == '🔓':
        mesid = payload.message_id
        chanid = payload.channel_id
        channel = bot.get_channel(chanid)
        s = await channel.fetch_message(mesid)
        await channel.send (decod(s.content))

@bot.command()
async def help(ctx):

    embed = discord.Embed(
        colour = discord.Colour.purple()
    )

    embed.set_author(name = 'Help')
    embed.add_field(name = 'Common commands', value='%clear - Delets messages\n%temp - gives the temperature in the chosen city(example: %temp Kyiv)\n%weather - gives the weather in the chosen city(example: %weather Kyiv)', inline=False)
    embed.add_field(name = 'Music commands', value='%join - makes bot join your voice channel\n%leave - makes bot leave voice channel\n%play - makes bot play music from link or name \n(example: %play https://www.youtube.com/watch?v=nybtOIxlku8)\n%playlist - makes bot play playlist from link (example is the same as %play)\n%queue - shows the current queue of the songs\n%pause - pauses the song\n%resume - resumes the song\n%skip - skips the song', inline=False)
    embed.add_field(name = 'Other commands', value='react on message with 🔓 to translate message from the English keyboard layout to Ukrainian', inline=False)

    await ctx.send(embed = embed)

@bot.command()
async def clear(ctx, arg):
    """function for deleting the messages"""

    try:
        amount = int(arg)
        print(f'successfully deleted {amount} messages')
        await ctx.channel.purge(limit=int(amount))

    except ValueError:
        await ctx.send('You need to ')

@bot.command()
async def temp(ctx, city):
    """giving the temperature in the chosen city"""

    lc,inf, tm = await weatherc(ctx, city)
    await ctx.send(tm + '°C')

@bot.command()
async def weather(ctx, city):

    """giving the weather in the chosen city"""

    lc,inf,tm = await weatherc(ctx, city)
    await ctx.send(lc)
    await ctx.send(inf)
    await ctx.send(tm + '°C')

async def setup():
    await bot.wait_until_ready()
    bot.add_cog(music(bot))


bot.loop.create_task(setup())
bot.run(token)
