import discord
from discord.ext import commands
import re
from decode import *
from defweather import *
import os,random
import time
from music import music
from botconfig import token

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='%', intents=intents)
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

    await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(payload):
    """function for translates message from the English keyboard layout to Ukrainian"""
    if payload.emoji.name == '🔓':
        mesid = payload.message_id
        chanid = payload.channel_id
        channel = bot.get_channel(chanid)
        s = await channel.fetch_message(mesid)
        await channel.send(decod(s.content))

@bot.command()
async def help(ctx):

    embed = discord.Embed(
        colour = discord.Colour.purple()
    )

    embed.set_author(name = 'Help')
    embed.add_field(name = 'Common commands', value='%clear - Delets messages\n%temp - gives the temperature in the chosen city(example: %temp Kyiv)\n%weather - gives the weather in the chosen city(example: %weather Kyiv)', inline=False)
    embed.add_field(name = 'Music commands', value='%leave - makes bot leave voice channel\n%play - makes bot play music from link or name also can play playlists (playlists only from link)\n(example: %play https://www.youtube.com/watch?v=nybtOIxlku8)\n%queue - shows the current queue of the songs\n%pause - pauses the song\n%resume - resumes the song\n%skip - skips the song(You can also specify how much songs you`d like to skip, example:%skip 5 (number is optional))\n%stop - to clear the music queue', inline=False)
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
    await bot.add_cog(music(bot))

async def main():
    async with bot:
        bot.loop.create_task(setup())
        await bot.start(token)

asyncio.run(main())
