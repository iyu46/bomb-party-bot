# main.py
# Written in Python 3.7.3

#sys: temp import
import sys
import os
import json
import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound

# define constants (be sure to set values in tokens.json before running!)
with open('config/tokens.json') as f:
    data = json.load(f)
BOT_TOKEN = data['bot_token']
API_KEY = data['bot_apiKey']
with open('resources/words_dictionary.json') as word_file:
    VALID_WORDS = set(word_file.read().split())
with open('resources/forbidden_three.json') as word_file:
    FORBIDDEN = set(word_file.read().split())

_ACTIVE_GAMES = {}

# format for _ACTIVE_GAMES:
# {
#   "CHANNEL ID" : "USER ID that called start()"
#   "CHANNEL ID_STATE" : "join" or "playing"
#   "CHANNEL ID_GOAL" : "integer from 1 to 50"
# }

def check_word(word):
    return bool(word in VALID_WORDS)

# Parameters:
#   key: key of _ACTIVE_GAMES dict
#   value: value of _ACTIVE_GAMES dict
#   append: string selector to mutate key into subkey (if it exists)
def activeGames_set(key, value, append):
    if append == "_GOALS" or "_STATE":
        _ACTIVE_GAMES[str(key) + append] = str(value)
        print('in _ACTIVE_GAMES, ' + str(key) + append + ' has been set to ' + str(value))
    else:
        _ACTIVE_GAMES[str(key)] = str(value)
        print('in _ACTIVE_GAMES, ' + str(key) + ' has been set to ' + str(value))
    return

def activeGames_get(key, append):
    if append == "_GOALS" or "_STATE":
        return _ACTIVE_GAMES[str(key) + append]
    else:
        return _ACTIVE_GAMES[str(key)]

def activeGames_check(key, append):
    if append == "_GOALS" or "_STATE":
        return str(key) + append in _ACTIVE_GAMES
    else:
        return str(key) in _ACTIVE_GAMES

def activeGames_pop(key, append):
    if append == "_GOALS" or "_STATE":
        _ACTIVE_GAMES.pop(str(key) + append)
    else:
        _ACTIVE_GAMES.pop(str(key))
    return

def activeGames_end(key):
    print('in _ACTIVE_GAMES, ' + str(key) + " will be cleared")
    if activeGames_check(key, ''):
        if activeGames_check(key, '_GOAL'):
            activeGames_pop(key, '_GOAL')
        if activeGames_check(key, '_STATE'):
            activeGames_pop(key, '_STATE')
        activeGames_pop(key, '')
    return

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

@bot.command(name='start', help='Starts a game. Only one game can be active at a given time in a channel.')
async def start(ctx):
    if activeGames_check(ctx.message.channel.id, ''):
        await ctx.send('Game is already in progress! Try starting the game in another channel?')
    else:
        #_ACTIVE_GAMES[str(ctx.message.channel.id)] = ctx.author.id
        activeGames_set(ctx.message.channel.id, ctx.author.id, '')

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit() and message.content > '0' and message.content <= '50'
        
        await ctx.send('A game of Bomb Party has been started by ' + ctx.message.author.mention + '! To how many points would you like to play until? Enter a number between 1-50.' )
        points = ''
        try:
            points = await bot.wait_for('message', timeout=30.0, check=check)
            points = points.content
            #_ACTIVE_GAMES[str(ctx.message.channel.id) + "_GOAL"] = points
            activeGames_set(ctx.message.channel.id, points, "_GOAL")
            #_ACTIVE_GAMES[str(ctx.message.channel.id) + "_STATE"] = "join"
            activeGames_set(ctx.message.channel.id, "join", "_STATE")
            await ctx.send('Point target has been set to ' + points + ". The game will begin in 30 seconds - type !bp join before the game starts to play (the owner must join as well)." )
        except asyncio.TimeoutError:
            #_ACTIVE_GAMES.pop(str(ctx.message.channel.id))
            activeGames_end(ctx.message.channel.id)
            await ctx.send('Timed out. Game has been terminated.' )
            return

@bot.command(name='end', help='Ends a game. Only the person who started the game can end it in a channel.')
async def end(ctx):
    if not activeGames_check(ctx.message.channel.id, ''): 
        await ctx.send('Game is not in progress in this channel!')
    elif activeGames_get(ctx.message.channel.id, '') != str(ctx.author.id):
        await ctx.send('Only the game owner can end the game in this channel!')
    else:
        #_ACTIVE_GAMES.pop(str(ctx.message.channel.id))
        activeGames_end(ctx.message.channel.id)
        await ctx.send('Game has successfully been terminated!')

@bot.command(name='rules', help='Shows the rules to Bomb Party.')
async def rules(ctx):
	em = discord.Embed(colour=0xF44336)
	em.add_field(name='Bomb Party Rules', value='Keep talking and nobody explodes.', inline='false')
	em.add_field(name='1.', value='All words are in the English dictionary.', inline='true')
	em.add_field(name='2.', value='Start the game by typing !bp start and enter the point goal. Afterwards, everyone who wants to play must type !bp join within 30 seconds.', inline='true')
	em.add_field(name='3.', value='The game will generate a random combination of three letters. When it\'s your turn, quickly enter any word that contains that combination of letters.', inline='true')
	em.add_field(name='The turn order is the order that users type !bp join.', value='Your turn begins when the bot mentions you. Just enter any word and if it\'s a valid word and contains the random letter combination, the bot will move on to the next person. Have fun!', inline='false')

	await ctx.send(embed=em)

@bot.command(name='exit', help='Stops script running on host system (debug).')
async def exit(ctx):
    await ctx.send("Ending process")
    sys.exit()

bot.run(BOT_TOKEN)