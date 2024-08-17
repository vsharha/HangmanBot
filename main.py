import discord
from discord.ext import commands
import random

bot = commands.Bot(command_prefix = commands.when_mentioned_or("hm ", "HM ", "Hm ", "hM "),case_insensitive=True)

@bot.event
async def on_ready():
    print("Initiated.")

helpColor = discord.Color.dark_green()

def embedLinks(embed):
    embed.add_field(name = "Links", value = "[Add Me](https://discord.com/api/oauth2/authorize?client_id=957028948867424368&permissions=0&scope=bot) • [Support Server](https://discord.gg/A25yw6a6vW) • [Vote for Me](https://top.gg/bot/957028948867424368)", inline = False)

@bot.event
async def on_guild_join(guild):
    onGuildJoin_msg = "The bot was added to a new server"
    try:
        embed = discord.Embed(description = "**Hello there!**", color = helpColor)
        embed.add_field(name = "Thank you for choosing HangmanBot.", value = "Use `hm help` to get help.", inline = False)
        embedLinks(embed)
        embed.set_footer(text = "Have fun!")
        welcomeChannel = guild.system_channel if guild.system_channel is not None else random.choice(guild.text_channels)
        await welcomeChannel.send(embed = embed)
    except:
        onGuildJoin_msg += " (Unable to send on_guild_join message)"
    print(onGuildJoin_msg)

helpCommand = (
        ("hm help", "See this message"),
        ("hm play", "Start a new multiplayer game or join somebody's game"),
        ("hm play random", "Start a new game with a random word"),
        ("hm hint", "Get a hint while in game"),
        ("hm cancel, hm stop", "Cancel a game")
)

class MyHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(description = "**Available commands:**", color = helpColor)
        for i in helpCommand:
            embed.add_field(name=f"• `{i[0]}`", value=i[1], inline = False)
        embedLinks(embed)
        embed.set_footer(text="hm help")
        await self.context.send(embed = embed)
bot.help_command = MyHelp()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.channel.send("You need to be in a server to use this command.")

class Game:
    def __init__(self):
        self.gameChannel = None
        self.player1 = None
        self.player2 = None
    
        self.word = None
        self.placeholder = None
    
        self.tries = 0
        
        self.hints = []
        
        self.mistakes = []
        self.plusOne = False

maxMistakes = 7
maxHints = 3

games = []

dev_ID = 0

@bot.command()
async def dev(ctx):
    if ctx.author.id == dev_ID:
        length = len(games)
        await ctx.channel.send(f"There {'is' if length == 1 else 'are'} {'no' if length == 0 else length} ongoing game{'s' if length != 1 else ''}.\n")

def getGameID(ctx):
    ID = None
    for i in games:
        if i.gameChannel == ctx.channel:
            ID = games.index(i)
    return ID

async def printHangman(ID):
    hangman = "=————————\n"
    hangman += "|   |\n"

    len_mistakes = len(games[ID].mistakes)

    prints = 0
    for i in range(4):
        if i == 0 and len_mistakes >= 1:
            hangman += "|   😳\n"
            prints += 1
        elif i == 1 and len_mistakes >= 2:
            if len_mistakes == 2:
                hangman += "|   |\n"
            elif len_mistakes == 3:
                hangman += "|  /|\n"
            else:
                hangman += "|  /|\\\n"
            prints += 1
        elif i == 2 and len_mistakes >= 5:
            hangman += "|   Ʌ\n"
            prints += 1
        elif i == 3 and len_mistakes >= 6:
            if len_mistakes == 6:
                hangman += "|  /\n"
            else:
                hangman += "|  / \\\n"
            prints += 1
    for i in range(4 - prints):
        hangman += "|\n"

    hangman += f"\n{games[ID].placeholder}"
    if len_mistakes != maxMistakes:
        footer = f"Mistakes: {len_mistakes}"
        if games[ID].plusOne:
            footer += " (+1)"
    elif games[ID].placeholder == games[ID].word:
        footer = "GG WP"
    else:
        footer = "GAME OVER!"

    embed = discord.Embed(description = f"```{hangman}```", color = discord.Color.purple())
    embed.set_footer(text=footer)
    await games[ID].gameChannel.send(embed = embed)

async def start_game(word, ID):
    games[ID].word = word
    games[ID].placeholder = "_" * len(word)
    await printHangman(ID)
    await games[ID].gameChannel.send(f"**{f'{games[ID].player2.mention}, m' if not games[ID].player1 == 'bot' else 'M'}ake a guess!** *(letter by letter or the whole word)*\nUse `hm hint` to get a hint.")

@bot.command()
async def play(ctx, arg = None):
    if arg is not None:
        arg = arg.casefold()

    if arg is None or arg == "random":
        ID = getGameID(ctx)
        if ID is None:
            games.append(Game())
            ID = games.index(games[-1])
            games[ID].gameChannel = ctx.channel
            if arg is None:
                if ctx.guild is not None:
                    games[ID].player1 = ctx.author
                    await ctx.channel.send("You are Player 1. Wait for someone else to join using `hm play` or use `hm cancel` to cancel.")
                else:
                    games.remove(games[ID])
                    raise commands.NoPrivateMessage
            elif arg == "random":
                games[ID].player1 = "bot"
                games[ID].player2 = ctx.author
                from words import words
                await start_game(random.choice(words), ID)
        elif arg is None and games[ID].player2 is None:
            if ctx.author != games[ID].player1 or ctx.author.id == dev_ID:
                games[ID].player2 = ctx.author
                await ctx.channel.send(f"You just joined as Player 2.\n{games[ID].player1.mention}, check your DMs, please.")
                await games[ID].player1.send("What word will Player 2 have to guess?")
            else:
                await ctx.channel.send("You are already playing as Player 1.")
        else:
            await ctx.channel.send("There is an ongoing game in this channel.")

def noGameError_msg(ctx):
    return f"You are not in a game in this channel.\nStart one using {'`hm play` or ' if ctx.guild is not None else ''}`hm play random`."

@bot.command(aliases=["stop"])
async def cancel(ctx):
    ID = getGameID(ctx)
    if ID is None:
        await ctx.channel.send(noGameError_msg(ctx))
    elif ctx.channel == games[ID].gameChannel:
        if ctx.author == games[ID].player1 or ctx.author == games[ID].player2:
            cancel_msg = "You cancelled the game."
            if ctx.author == games[ID].player2 and games[ID].word is not None:
                cancel_msg += f" The word was \"{games[ID].word}\"."
            await ctx.channel.send(cancel_msg)
            games.remove(games[ID])

@bot.command()
async def hint(ctx):
    ID = getGameID(ctx)
    if ID is None:
        await ctx.channel.send(noGameError_msg(ctx))
    elif ctx.channel == games[ID].gameChannel and ctx.author == games[ID].player2 and games[ID].word is not None:
        len_hints = len(games[ID].hints)
        if len_hints <= maxHints:
            if [i for i in games[ID].placeholder].count("_") > 1:
                check = games[ID].placeholder + ''.join(games[ID].hints)
                chars = [i for i in games[ID].word]
                hint = "_"
                while hint in check:
                    hint = random.choice(chars)
                games[ID].hints.append(hint)
                len_hints += 1
                left = "No" if maxHints == len_hints else maxHints-len_hints
                await games[ID].gameChannel.send(f"Hint: **{hint}**\n*({left} hint{'s' if left != 1 else ''} left)*")
            else:
                await games[ID].gameChannel.send("Only 1 letter is left, I bet you could guess that yourself.")
        else:
            await games[ID].gameChannel.send("*You used all your hints!*")

@bot.event
async def on_message(ctx):
    await bot.process_commands(ctx)
    
    if ctx.guild is None:
        ID = None
        for i in games:
            if i.player1 == ctx.author:
                ID = games.index(i)

        if ID is not None and ctx.author == games[ID].player1 and games[ID].player2 is not None:
            word = ctx.content.casefold()
            if word.isalpha():
                games[ID].player1 = None
                await start_game(word, ID)
            else:
                games[ID].word = None
                await games[ID].player1.send("Enter a word consisting of letters and without spaces.")

    ID = getGameID(ctx)
    
    if ID is not None and ctx.author == games[ID].player2 and games[ID].word is not None:
        guess = ctx.content.casefold()
        if (len(guess) == 1 and guess.isalpha()) or guess == games[ID].word:
            games[ID].tries += 1
            if games[ID].plusOne:
                games[ID].plusOne = False
            if guess == games[ID].word:
                games[ID].placeholder = games[ID].word
            else:
                if guess in games[ID].word:
                    indexes = []
                    for i, j in enumerate(games[ID].word):
                        if j == guess:
                            indexes.append(i)
                    tempPlaceholder = list(games[ID].placeholder)
                    for i in indexes:
                        tempPlaceholder[i] = guess
                    games[ID].placeholder = "".join(tempPlaceholder)
                elif guess not in games[ID].mistakes:
                    games[ID].mistakes.append(guess)
                    games[ID].plusOne = True
                
            len_mistakes = len(games[ID].mistakes)
            print
            await printHangman(ID)
            if games[ID].placeholder == games[ID].word or len_mistakes == maxMistakes:
                if games[ID].placeholder == games[ID].word:
                    color = discord.Color.green()
                    title = ":-)"
                    results = ""
                    
                    string = f"You got it right on the {games[ID].tries}th try!\n"
                    check = games[ID].tries % 10
                    if 1 <= check <= 3 and not 11 <= games[ID].tries % 100 <= 13:
                        string = string.replace("th ", ("st" if check == 1 else "nd" if check == 2 else "rd") + " ")
                    results += string
                    
                    if len_mistakes == 0:
                        results += "No mistakes were made during the game."
                    elif len_mistakes == 1:
                        results += "You only made one mistake."
                    elif maxMistakes - len_mistakes == 1:
                        results += "You were 1 step away from the disaster!"
                    else:
                        results += f"{maxMistakes - len_mistakes} more mistakes and we would have a hangman!"
                    footer = "You are a good guesser!"
                    
                elif len_mistakes == maxMistakes:
                    color = discord.Color.red()
                    title = ":-("
                    results = f"You lost.\nThe word {'I' if games[ID].player1 == 'bot' else 'Player 1'} chose for you was \"{games[ID].word}\""
                    footer = "Better luck next time."

                embed = discord.Embed(title = title, description = results, color = color)
                embed.add_field(name = "Ready for a rematch? Need help?", value = f"Use {'`hm play` or ' if ctx.guild is not None else ''}`hm play random` to start a new game, use `hm help` to get help", inline = False)
                embedLinks(embed)
                embed.set_footer(text = footer)
                await games[ID].gameChannel.send(embed = embed)

                games.remove(games[ID])      

from keep_alive import keep_alive
keep_alive()

import os
try:
    bot.run(os.environ["TOKEN"])
except discord.errors.HTTPException as HTTPException:
    if HTTPException.status == 429:
        print("The bot is being rate limited, trying to restart")
        os.system("kill 1")
        os.system("python restarter.py")
    else:
        raise
