import discord
from discord.ext import commands
from decode import *
from defweather import *
from music import music
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='%', intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching,name="Something")
    await bot.change_presence(activity=activity)
    print("Bot is ready!")

@bot.command()
async def help(ctx):

    embed = discord.Embed(
        colour = discord.Colour.purple()
    )

    embed.set_author(name = 'Help')
    embed.add_field(name = 'Common commands', value='%clear - Delets messages\n%temp - gives the temperature in the chosen city(example: %temp Kyiv)\n%weather - gives the weather in the chosen city(example: %weather Kyiv)', inline=False)
    embed.add_field(name = 'Music commands', value='\n%leave - makes bot leave voice channel\n%play - makes bot play music from link or name also can play playlists (playlists only from link)\n(example: %play https://www.youtube.com/watch?v=nybtOIxlku8)\n%queue - shows the current queue of the songs\n%skip - skips the song(You can also specify how much songs you`d like to skip, example:%skip 5 (number is optional))\n%stop - to clear the music queue', inline=False)

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
        await bot.start('token') # paste your token instead
        await bot.add_cog(music(bot))

asyncio.run(main())
