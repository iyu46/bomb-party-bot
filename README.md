# bomb-party-bot
# This bot allows users to play the Bomb Party word game in Discord.

The Bomb Party word game is originally created and hosted at http://bombparty.sparklinlabs.com/. No credit is taken for the concept.

JSON english library from [dwyl/english-words](https://github.com/dwyl/english-words).

Forbidden three (least likely trigrams in English) from [rlvaugh/Impractical_Python_Projects](https://github.com/rlvaugh/Impractical_Python_Projects), Chapter 3.

## Requirements
``` pip install -r requirements.txt ```

## How to Play

Bomb Party is a game about quickly coming up with words that contain a given set of letters - if you don't think of one quickly enough, you lose health. If you do, you gain a point. The game goes on, rapidly changing between players, until one person reaches the point goal or everybody loses all their health.

To start a game, type !bp start, then type !bp join. The game is fully multiplayer, so everyone who wants to play in a given round must type !bp join as well when prompted. The game will automatically start after 30 seconds or if the game leader types !bp skip. Players will take turns answering the bot's questions.

![example 1](https://github.com/Kaillus/bomb-party-bot/blob/master/readme_img/help3.gif)

![example 2](https://github.com/Kaillus/bomb-party-bot/blob/master/readme_img/help2.png)

# Commands

```!bp``` to see all available commands

![example 3](https://github.com/Kaillus/bomb-party-bot/blob/master/readme_img/help1.png)

```!bp help [command]``` to see help info available for that command
