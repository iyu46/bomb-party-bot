# main.py
# Written in Python 3.7.3

import os
import json
#sys: temp import
import sys
import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound

# define constants (be sure to set values in tokens.json before running!)
with open('config/tokens.json') as f:
    data = json.load(f)
BOT_TOKEN = data['bot_token']
API_KEY = data['bot_apiKey']
SERVER_ID = -1 #insert server ID here
BOT_ID = -1 #insert bot ID here
with open('resources/words_dictionary.json') as word_file:
    VALID_WORDS = set(word_file.read().split())

bot = commands.Bot(command_prefix='!bp ')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    with open('config/config.json') as f:
        inp = json.load(f)

@bot.command(name='active', help='Sets whether or not the bot is currently active.')
async def active(ctx, state):
    # import saved configs in session
    with open('config/config.json') as f:
        inp = json.load(f)
    # try-catch check and convert input parameter to boolean, catch and end if invalid
    try:
        if state == "on": 
            s = True
        elif state == "off":
            s = False
        else:
            await ctx.send('Input state is invalid')
            return
    except CommandNotFound:
        await ctx.send('Input state is invalid')
        return
    # compare input state to saved state and perform action
    if s == inp['active']:
        response = "active is already %s!" % s
        await ctx.send(response.lower())
    else:
        newdata = { "active": s }
        with open('config/config.json', 'w') as outfile:
            json.dump(newdata, outfile)
        response = "active has been set to %s!" % s
        await ctx.send(response.lower())


@bot.command(name='exit', help='Stops script running on host system (debug).')
async def exit(ctx):
    await ctx.send("Ending process")
    sys.exit()

bot.run(BOT_TOKEN)