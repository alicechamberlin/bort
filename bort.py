import discord
from discord.ext import commands
from discord.ext.commands import Bot
import random
import datetime
import json
import inspect
import os

config = {}
with open('config/config.json','r') as f:
    config = json.load(f)

OWNER_ID = config["ownerId"]
TOKEN = config["token"]
BOT_PREFIX = ("?")
COGS_DIR = 'cogs'

intents = discord.Intents.default()
intents.members=True
intents.presences=True

bot = Bot(command_prefix=BOT_PREFIX, intents=intents)

if __name__ == '__main__':
    for file in os.listdir(COGS_DIR):
        if file.endswith('.py'):
            try:
                bot.load_extension(COGS_DIR + '.' + file[:-3])
                print('{} was loaded.'.format(file[:-3]))
            except Exception as error:
                print('{} cannot be loaded. [{}]'.format(file[:-3], error))

@bot.event
async def on_ready():
    print('------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(datetime.datetime.now().strftime('%m/%d %I:%M:%S %p'))
    print('------')

@bot.command(hidden = True)
async def r(ctx):
    if ctx.author.id == OWNER_ID:
        await ctx.send('bye')
        await bot.close()

async def bot_exec(ctx, strCode):

    results = []
    memory = []
    codes = strCode.strip('` ').split(";")
    python = '```py\n{}\n```'
    env = {
        'bot': bot,
        'ctx': ctx,
        'message': ctx.message,
        'guild': ctx.guild,
        'channel': ctx.channel,
        'author': ctx.author,
        'results' : results,
        'memory' : memory,
        'codes' : codes
    }

    env.update(globals())

    for code in codes:
        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result
            results.append(result)
            if type(result) == discord.Embed:
                await ctx.send(embed=result)
            else:
                await ctx.send(str(python.format(result)))
        except Exception as e:
            await ctx.send(python.format(type(e).__name__ + ': ' + str(e)))

@bot.command(hidden=True)
async def debug(ctx, *, strCode : str):
    if (ctx.author.id != OWNER_ID):
        return
    await bot_exec(ctx, strCode)

@bot.event
async def on_message_edit(before, after):
    await bot.invoke(await bot.get_context(after))

bot.run(TOKEN)
