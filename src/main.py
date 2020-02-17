# main.py
# Written in Python 3.7.3

#sys: temp import
import sys
import os
from collections import OrderedDict 
import string
import random
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
with open('resources/words_dictionary.json') as word_file1:
    VALID_WORDS = set(word_file1.read().split())
with open('resources/forbidden_three.json') as word_file:
    LOWER_ALPHABET = string.ascii_lowercase
    LOWER_ALPHABET = LOWER_ALPHABET.strip('y')
    VOWELS = ['a', 'e', 'i', 'o', 'u', 'y']
    FORBIDDEN = set(word_file.read().split())

_ACTIVE_GAMES = {}

# format for _ACTIVE_GAMES:
# {
#   "CHANNEL ID" : "USER ID that called start()"
#   "CHANNEL ID_STATE" : "join" or "playing"
#   "CHANNEL ID_GOAL" : "integer from 1 to 50"
#   "CHANNEL ID_PLAYERS" : {} key: "USER ID", value: OrderedDict()["points", "health"]
# }

def check_word(word):
    wordCheck = "\"" + word + "\":"
    return wordCheck in VALID_WORDS

def generateTrigram():
    ran = [1, 2]
    dom = random.choice(ran)
    if dom == 1:
        trigram = random.choice(LOWER_ALPHABET) + random.choice(VOWELS) + random.choice(LOWER_ALPHABET)
    else:
        trigram = random.choice(VOWELS) + random.choice(LOWER_ALPHABET) + random.choice(VOWELS)
        if trigram[1] in random.choice(VOWELS):
            return generateTrigram()
    if not trigram in FORBIDDEN:
        return trigram
    else:
        print(trigram + " was generated, rerolling")
        generateTrigram()

# Parameters:
#   key: key of _ACTIVE_GAMES dict
#   value: value of _ACTIVE_GAMES dict
#   append: string selector to mutate key into subkey (if it exists)
def activeGames_set(key, value, append):
    if append == "_PLAYERS":
        _ACTIVE_GAMES[str(key) + append] = value
    elif append: #catches every other append
        _ACTIVE_GAMES[str(key) + append] = str(value)
        print('in _ACTIVE_GAMES, ' + str(key) + append + ' has been set to ' + str(value))
    else:
        _ACTIVE_GAMES[str(key)] = str(value)
        print('in _ACTIVE_GAMES, ' + str(key) + ' has been set to ' + str(value))
    return

def activeGames_get(key, append):
    if append in ["_GOAL", "_STATE", "_PLAYERS"]:
        return _ACTIVE_GAMES[str(key) + append]
    else:
        return _ACTIVE_GAMES[str(key)]

def activeGames_check(key, append):
    if append in ["_GOAL", "_STATE", "_PLAYERS"]:
        return str(key) + append in _ACTIVE_GAMES
    else:
        return str(key) in _ACTIVE_GAMES

def activeGames_pop(key, append):
    if append in ["_GOAL", "_STATE", "_PLAYERS"]:
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
        if activeGames_check(key, '_PLAYERS'):
            activeGames_pop(key, '_PLAYERS')
        activeGames_pop(key, '')
    return

bot = commands.Bot(command_prefix='!bp ')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    with open('config/config.json') as f:
        inp = json.load(f)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    ctx = await bot.get_context(message)

    if str(message.content).strip() == "!bp":
        await commands(ctx)
        return

    if str(ctx.prefix).strip() == "!bp":
        if ctx.command is None:
            await commands(ctx)
            return

    await bot.process_commands(message)

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
        activeGames_set(ctx.message.channel.id, ctx.author.id, '')

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit() and message.content > '0' and message.content <= '300'
        
        await ctx.send('A game of Bomb Party has been started by ' + ctx.message.author.name + '! To how many points would you like to play until? Enter a number between 1-300.' )
        points = ''
        try:
            points = await bot.wait_for('message', timeout=15.0, check=check)
            points = points.content
            activeGames_set(ctx.message.channel.id, points, "_GOAL")
            activeGames_set(ctx.message.channel.id, "join", "_STATE")
            await ctx.send('Point target has been set to ' + points + ". The game will begin in 30 seconds - type !bp join before the game starts to play (the owner must join as well). Type !bp skip to force-start the game." )
            players = {}
            activeGames_set(ctx.message.channel.id, players, "_PLAYERS")
            await join_time(ctx)
        except asyncio.TimeoutError:
            activeGames_end(ctx.message.channel.id)
            await ctx.send('Timed out. Game has been terminated.' )
            return

@bot.command(name='join', help='Join the game in the channel. Game must be in the joining phase.')
async def join(ctx):
    if activeGames_check(ctx.message.channel.id, '_STATE') and activeGames_get(ctx.message.channel.id, '_STATE') == "join":
        stats = OrderedDict()
        stats['points'] = 0
        stats['health'] = 3
        activeGames_get(ctx.message.channel.id, "_PLAYERS")[str(ctx.author.id)] = stats
        print('Player ' + str(ctx.author.id) + ' was registered for game in ' + str(ctx.message.channel.id) + ' with values ' + str(activeGames_get(ctx.message.channel.id, "_PLAYERS")[str(ctx.author.id)]['points']) + ', ' + str(activeGames_get(ctx.message.channel.id, "_PLAYERS")[str(ctx.author.id)]['health']))
        await ctx.send(ctx.message.author.name + ' has joined the game!')
    else:
        await ctx.send('Game state is invalid!')


async def join_time(ctx):
    def check(message):
        if message.content == "!bp skip":
            raise asyncio.TimeoutError
        return message.content == "!bp end"
    try:
        response = await bot.wait_for('message', timeout=15.0, check=check)
        await end(ctx)
    except asyncio.TimeoutError:
        if activeGames_get(ctx.message.channel.id, "_PLAYERS"):
            await ctx.send('Game is starting!' )
            await game_init(ctx)
        else:
            activeGames_end(ctx.message.channel.id)
            await ctx.send('Timed out due to no players. Game has been terminated.')



async def game_init(ctx):
    activeGames_set(ctx.message.channel.id, 'playing', '_STATE')
    #await ctx.send('game init' )
    await game(ctx)


async def game(ctx):
    while True:
        for player in activeGames_get(ctx.message.channel.id, "_PLAYERS"):
            if not activeGames_get(ctx.message.channel.id, "_PLAYERS")[str(player)]['health'] == 0:
                mention = '<@' + str(player) + '>'
                trigram = generateTrigram()
                #trigram = "ass"
                em = discord.Embed(colour=0x22AA44)
                em.add_field(name='Bomb Party!', value='Keep talking and nobody explodes.', inline='false')
                em.add_field(name='Goal', value=str(activeGames_get(ctx.message.channel.id, "_GOAL")), inline='true')
                em.add_field(name='Points', value=str(activeGames_get(ctx.message.channel.id, "_PLAYERS")[str(player)]['points']), inline='true')
                em.add_field(name='Health', value=str(activeGames_get(ctx.message.channel.id, "_PLAYERS")[str(player)]['health']), inline='true')
                em.add_field(name='Type !bp kill to leave the game.', value='For emergencies and stuff.', inline='false')
                msg = mention + ", it's your turn! Write a word that contains " + str(trigram.upper() + ". Longer words give you more points!")
                await ctx.send(msg, embed = em)
                
                def check(message):
                    return trigram in message.content.lower() and check_word(message.content.lower().strip()) and message.author.id == int(player)
                
                try:
                    response = await bot.wait_for('message', timeout=10.0, check=check)
                    points = len(response.content) - 2
                    msg2 = "Nice! " + ctx.message.author.name + " gained " + str(points) + " point"
                    if points > 1:
                        msg2 = msg2 + 's'
                    msg2 = msg2 + '.'
                    await ctx.send(msg2)
                    activeGames_get(ctx.message.channel.id, "_PLAYERS")[str(player)]['points'] += points
                    if activeGames_get(ctx.message.channel.id, "_PLAYERS")[str(player)]['points'] >= int(activeGames_get(ctx.message.channel.id, "_GOAL")):
                        await ctx.send("Congratulations! " + mention + " wins this game of Bomb Party.")
                        activeGames_set(ctx.message.channel.id, -1, "_GOAL")
                        break
                except asyncio.TimeoutError:
                    await ctx.send("Ran out of time! " + ctx.message.author.name + " lost 1 health.")
                    activeGames_get(ctx.message.channel.id, "_PLAYERS")[str(player)]['health'] -= 1
                    if activeGames_get(ctx.message.channel.id, "_PLAYERS")[str(player)]['health'] == 0:
                        await ctx.send("Oh no, " + ctx.message.author.name + "! You have blown up. Better luck next time!")


        # if goal was reached (goal is set to -1 after victory)
        if int(activeGames_get(ctx.message.channel.id, "_GOAL")) == -1:
            activeGames_end(ctx.message.channel.id)
            break

        # if everyone is dead
        numPlayers = len(activeGames_get(ctx.message.channel.id, "_PLAYERS"))
        numDead = 0
        for player in activeGames_get(ctx.message.channel.id, "_PLAYERS"):
            if activeGames_get(ctx.message.channel.id, "_PLAYERS")[str(player)]['health'] == 0:
                numDead += 1
        if numDead == numPlayers:
            await ctx.send("Oh no! It looks like everybody has blown up. Nobody wins this game of Bomb Party.")
            activeGames_end(ctx.message.channel.id)
            break


@bot.command(name='kill', help='Kills you in the game.')
async def kill(ctx):
    if not activeGames_get(ctx.message.channel.id, '_STATE') == "playing": 
        await ctx.send('Game is not in correct state!')
    else:
        if str(ctx.message.author.id) in activeGames_get(ctx.message.channel.id, "_PLAYERS"):
            activeGames_get(ctx.message.channel.id, "_PLAYERS")[str(ctx.author.id)]['health'] = 0
            await ctx.send('You have been Thanos snapped.')


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
	em.add_field(name='Bomb Party Rules', value='Keep talking and nobody explodes. Created by kail#1968 on Discord', inline='false')
	em.add_field(name='1.', value='Start the game by typing !bp start and enter the point goal. Afterwards, everyone who wants to play must type !bp join within 30 seconds.', inline='true')
	em.add_field(name='2.', value='The game will generate a random combination of three letters. When it\'s your turn, quickly enter any word that contains that combination of letters.', inline='true')
	em.add_field(name='3.', value='All words are in the English dictionary.', inline='true')
	em.add_field(name='The turn order is the order that users type !bp join.', value='Your turn begins when the bot mentions you. Just enter any word and if it\'s a valid word and contains the random letter combination, you\'ll get points and the bot will move on to the next person. Have fun!', inline='false')

	await ctx.send(embed=em)

@bot.command(name='skip', help='Skips the rest of the join phase.')
async def skip(ctx):
    return

@bot.command(name='info', help='Shows the rules.')
async def info(ctx):
    await rules(ctx)

@bot.command(name='commands', help='Lists the commands.')
async def commands(ctx):
	em = discord.Embed(colour=0xF44336)
	em.add_field(name='Bomb Party Bot', value='Created by kail#1968 on Discord, github.com/Kaillus', inline='false')
	em.add_field(name='Game-specific commands', value='start\njoin\nskip\nkill\nend', inline='true')
	em.add_field(name='Other', value='active\ncommands\nhelp\ninfo\nrules', inline='true')

	await ctx.send(embed=em)

@bot.command(name='exit', help='Stops script running on host system (debug).')
async def exit(ctx):
    await ctx.send("Ending process")
    sys.exit()

bot.run(BOT_TOKEN)