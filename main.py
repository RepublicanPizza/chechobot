import asyncprawcore
import discord
from discord import Embed
from discord.errors import NotFound
from discord.ext import commands
from requests import HTTPError
from youtube_dl import YoutubeDL
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import random as ran
import os
import time
import asyncpraw

# -------------------------------- Parameters ----------------------------------#
PLAYLIST = False
INDEX = 0
QUEUE = []
ID = 0
playing = False
LOOP = False
TIME = 0
key = os.environ["DISCORD"]
first_df = pd.read_csv("to-ZETW.csv", dtype="unicode")
second_df = pd.read_csv("AF-to-IT.csv", dtype="unicode")
All = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '!', '#', '$', '%', '&', '(', ')', '+', '/', ":"]
# s_list = []

# -------------------------------- Spotify / Reddit ---------------------------------#
CLIENT_ID = os.environ["SPOTIFY-ID"]
CLIENT_SECRET = os.environ["SPOTIFY-SECRET"]
REDIRECT = "http://example.com"
SCOPE = "playlist-read-private"
Reddit_id = os.environ["Reddit_id"]
Reddit_secret = os.environ["Reddit_secret"]
Reddit_agent = os.environ["Reddit_agent"]

reddit = asyncpraw.Reddit(client_id=Reddit_id, client_secret=Reddit_secret, user_agent=Reddit_agent)

credentials = spotipy.oauth2.SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

authorization = SpotifyOAuth(client_id=credentials.client_id, client_secret=credentials.client_secret,
                             redirect_uri=REDIRECT, cache_path=".cache", scope=SCOPE)

Client = spotipy.client.Spotify(auth=authorization.get_cached_token()["access_token"],
                                requests_timeout=10, retries=10)


def refresh():
    global Client

    token_info = authorization.refresh_access_token(authorization.get_cached_token()['refresh_token'])
    token = token_info["access_token"]
    Client = spotipy.client.Spotify(auth=token, requests_timeout=10, retries=10)


def getTracks(url):
    global PLAYLIST, QUEUE
    if "www.youtube.com" in url:
        PLAYLIST = False
        url = url[32:43]
        youtube_op = {"format": "bestaudio", "noplaylist": "True", "--age-limit": 25}
        with YoutubeDL(youtube_op) as yt:
            try:
                info = yt.extract_info("ytsearch:%s" % f"{url}", download=False)["entries"][0]
            except Exception:
                print("Error")
            else:
                url = info["formats"][0]["url"]
                title = info["title"]
                duration = info["duration"]
                time = sec_a_MinSec(duration)
                QUEUE.append([title, time, url])
    elif "open.spotify.com/track" in url:
        try:
            PLAYLIST = False
            search = Client.track(f"{url}")
            TRACK_TIME = mils_to_MinSec(search["duration_ms"])
            TRACK_ARTIST = search["artists"]
            if len(TRACK_ARTIST) > 0:
                TRACK_ARTIST = TRACK_ARTIST[0]["name"]
            elif len(TRACK_ARTIST) == 0:
                TRACK_ARTIST = search["artists"]["name"]
            TRACK_NAME = search["name"]
            TRACK = TRACK_ARTIST + " " + TRACK_NAME
            QUEUE.append([TRACK, TRACK_TIME])

        except spotipy.exceptions.SpotifyException or HTTPError or TypeError:
            refresh()
            getTracks(url)

    elif "open.spotify.com/playlist" in url:
        try:
            PLAYLIST = True
            search = Client.playlist_tracks(f"{url}")
            for n in range(0, len(search["items"])):
                TRACK_ARTIST = search["items"][n]["track"]["artists"]
                if len(TRACK_ARTIST) > 0:
                    TRACK_ARTIST = TRACK_ARTIST[0]["name"]
                else:
                    TRACK_ARTIST = search["items"][n]["track"]["artists"]["name"]
                TRACK_NAME = search["items"][n]["track"]["name"]
                TRACK_TIME = mils_to_MinSec(search["items"][n]["track"]["duration_ms"])
                TRACK = TRACK_ARTIST + " " + TRACK_NAME
                QUEUE.append([TRACK, TRACK_TIME])

        except spotipy.exceptions.SpotifyException or HTTPError or TypeError:
            refresh()
            getTracks(url)

    elif "open.spotify.com/album" in url:
        try:
            PLAYLIST = True
            search = Client.album_tracks(f"{url}")
            for n in range(0, len(search["items"])):
                TRACK_ARTIST = search["items"][n]["artists"]
                if len(TRACK_ARTIST) > 0:
                    TRACK_ARTIST = TRACK_ARTIST[0]["name"]
                else:
                    TRACK_ARTIST = search["items"][n]["artists"]["name"]
                TRACK_NAME = search["items"][n]["name"]
                TRACK = TRACK_ARTIST + " " + TRACK_NAME
                TRACK_TIME = mils_to_MinSec(search["items"][n]["duration_ms"])
                QUEUE.append([TRACK, TRACK_TIME])

        except spotipy.exceptions.SpotifyException or HTTPError or TypeError:
            refresh()
            getTracks(url)
    else:
        PLAYLIST = False
        youtube_op = {"format": "bestaudio", "noplaylist": "True", "--age-limit": 25}
        with YoutubeDL(youtube_op) as yt:
            try:
                info = yt.extract_info("ytsearch:%s" % f"{url}", download=False)["entries"][0]
            except Exception:
                print("Error")
            else:
                url = info["formats"][0]["url"]
                title = info["title"]
                duration = info["duration"]
                time = sec_a_MinSec(duration)
                QUEUE.append([title, time, url])


def mils_to_MinSec(tem):
    time_ms = int(tem) // 1000
    time_min = time_ms // 60
    time_sec = time_ms % 60
    if time_sec < 10:
        TRACK_TIME = f"{time_min}:0{time_sec}"
    else:
        TRACK_TIME = f"{time_min}:{time_sec}"
    return TRACK_TIME


def sec_a_MinSec(tem):
    min = int(tem) // 60
    sec = int(tem) % 60
    if sec < 10:
        duration = f"{min}:0{sec}"
    else:
        duration = f"{min}:{sec}"
    return duration


def save(song):
    try:
        with open(file="data.txt", mode="r", encoding="utf-8") as file:
            copy = file.read().splitlines()
            copy.append(song)
    except FileNotFoundError:
        with open(file="data.txt", mode="w", encoding="utf-8") as file:
            file.write(f"{song}\n")
    else:
        with open(file="data.txt", mode="w", encoding="utf-8") as file:
            for item in copy:
                file.write(f"{item}\n")


# -------------------------------- Discord  ----------------------------------#
client = commands.Bot(command_prefix=".")
client.remove_command("help")


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game("Listening to .help"))
    # await load_subredits()


@client.command(name="ping", help="Shows the bot's latency", aliases=["Ping"])
async def ping(ctx):
    await send_embed(ctx, f"Pong! {round(client.latency * 1000)}ms", 40)


async def send_embed(ctx, author: str, delete: int = None):
    embed = Embed(color=discord.Colour.orange())
    embed.set_author(name=author)
    await ctx.send(embed=embed, delete_after=delete)


# -------------------------------- Play CMD ----------------------------------#

@client.command(name="p", help="Searches and plays the song by title or YT url or Spotify Url",
                aliases=["pone", "play"])
async def p(ctx, *, args):
    global playing, INDEX, PLAYLIST, QUEUE
    if not playing:
        try:
            user = ctx.message.author
            vc = user.voice.channel
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        except AttributeError:
            await send_embed(ctx, "You must be connected to a voice channel first", 40)
        else:
            if voice is None:
                await vc.connect()
                getTracks(args)
                await play_music(ctx)
            elif voice.channel and voice.channel == vc:
                getTracks(args)
                await play_music(ctx)
    else:
        user = ctx.message.author
        vc = user.voice.channel
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if voice.channel != vc:
            await send_embed(ctx, "Already playing on another channel", 40)
        elif voice.channel == vc and not PLAYLIST:
            getTracks(args)
            item = len(QUEUE) - 1
            await send_embed(ctx, f" '{QUEUE[item][0]}' added to queue", 120)
        elif voice.channel == vc and PLAYLIST:
            getTracks(args)
            await send_embed(ctx, "Playlist added to queue", 120)


async def play_music(ctx):
    global INDEX, ID
    embed = Embed(color=discord.Color.orange())
    play_next(ctx)
    embed.set_author(name=f"Currently playing: {QUEUE[INDEX - 1][0]}")
    after = After(QUEUE[INDEX - 1][1]) + 10
    message = await ctx.send(embed=embed, delete_after=after)
    ID = message.id


def play_next(ctx):
    global playing, INDEX, QUEUE, LOOP, TIME
    if INDEX == len(QUEUE) and LOOP:
        INDEX = 0

    if len(QUEUE) > INDEX:
        ff_op = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", "options": "-vn"}
        if len(QUEUE[INDEX]) == 3:
            url = QUEUE[INDEX][2]
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
            voice.play(source=discord.FFmpegPCMAudio(url, **ff_op), after=lambda e: play_next(ctx))
            save(QUEUE[INDEX][0])
            playing = True
            INDEX += 1
            TIME = time.time()
        elif len(QUEUE[INDEX]) == 2:
            url = downloadSpoti(INDEX)
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
            voice.play(source=discord.FFmpegPCMAudio(url, **ff_op), after=lambda e: play_next(ctx))
            save(QUEUE[INDEX][0])
            playing = True
            INDEX += 1
            TIME = time.time()
    else:
        playing = False


def downloadSpoti(INDEX):
    global QUEUE
    youtube_op = {"format": "bestaudio", "noplaylist": "True", "--age-limit": 25}
    with YoutubeDL(youtube_op) as yt:
        try:
            info = yt.extract_info("ytsearch:%s" % f"{QUEUE[INDEX][0]}", download=False)["entries"][0]
            url = info["formats"][0]["url"]
        except Exception:
            print(None)
        else:
            return url


def After(time):
    sec = int(time[len(time) - 2:])
    min = int(time[0:time.find(":")])
    return sec + min * 60


@client.event
async def on_message_delete(message):
    global INDEX, playing, ID
    if message.author == client.user and playing and message.id == ID:
        embed = Embed(color=discord.Color.orange())
        embed.set_author(name=f"Currently playing: {QUEUE[INDEX - 1][0]}")
        after = After(QUEUE[INDEX - 1][1]) + 10
        message = await message.channel.send(embed=embed, delete_after=after)
        ID = message.id


@client.command(name="pause", help="Pauses the current song", aliases=["para"])
async def pause(ctx):
    global playing
    if playing:
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        voice.pause()
        playing = False


@client.command(name="resume", help="Resumes the current song", aliases=["segui"])
async def resume(ctx):
    global playing
    if not playing:
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        voice.resume()
        playing = True


@client.command(name="skip", help="Skips the current song (the amount of songs to skip can be specified)",
                aliases=["next"])
async def skip(ctx, amount: int = 1):
    global playing, INDEX, ID
    if playing:
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        voice.pause()
        message = await ctx.fetch_message(id=ID)
        INDEX += amount - 1
        play_next(ctx)
        await message.delete(delay=None)


@client.command(name="back", help="Goes back to the last song played", aliases=["atras"])
async def back(ctx):
    global INDEX
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if playing and INDEX > 1:
        voice.pause()
        INDEX -= 2
        try:
            message = await ctx.fetch_message(id=ID)
        except NotFound:
            print(None)
        else:
            await message.delete(delay=None)
        play_next(ctx)
    elif playing and INDEX == 1:
        voice.pause()
        INDEX -= 1
        try:
            message = await ctx.fetch_message(id=ID)
        except NotFound:
            print(None)
        else:
            await message.delete(delay=None)
        play_next(ctx)


@client.command(name="stop", help="Stops the current song(clears the queue)", aliases=["cortala"])
async def stop(ctx):
    global ID
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.pause()
    try:
        message = await ctx.fetch_message(id=ID)
    except NotFound:
        print(None)
    else:
        resetVariables()
        await message.delete(delay=None)
    await send_embed(ctx, "Stoped playing music", 40)


@client.command(name="leave", help="Leaves the current voice channel", aliases=["sali", "andate", "tomatela"])
async def leave(ctx):
    global playing, INDEX
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice is not None:
        voice.stop()
        await voice.disconnect()
        try:
            message = await ctx.fetch_message(id=ID)
        except NotFound:
            print(None)
        else:
            await message.delete(delay=None)
        resetVariables()
    elif voice is None:
        await send_embed(ctx, "Can't use that command right now", 40)


def resetVariables():
    global PLAYLIST, INDEX, QUEUE, ID, playing, LOOP
    PLAYLIST = False
    INDEX = 0
    QUEUE = []
    ID = 0
    playing = False
    LOOP = False


# --------------------------------------------------------------------------------------------------------------------#

@client.command(name="q", help="Shows the queue", aliases=["cola"])
async def q(ctx):
    global QUEUE, INDEX
    embed = Embed(color=discord.Colour.orange())
    embed.set_author(name="Queue")
    if len(QUEUE) > 0:
        for i in range(0, len(QUEUE)):
            if i == INDEX - 1:
                embed.add_field(name="Current", value=f" '{QUEUE[i][0]}' Duration: {QUEUE[i][1]}", inline=True)
            else:
                embed.add_field(name=f"{i}", value=f" '{QUEUE[i][0]}' Duration: {QUEUE[i][1]}", inline=True)
        await ctx.send(embed=embed, delete_after=120)
    else:
        await send_embed(ctx, "No music in the queue", 40)


@client.command(name="loop", help="Loops the current queue", aliases=["loopea"])
async def loop(ctx):
    global LOOP
    if len(QUEUE) > 0:
        LOOP = True
        await send_embed(ctx, "Playlist looped", 40)


@client.command(name="unloop", help="Unloops the current queue", aliases=["desloopea"])
async def unloop(ctx):
    global LOOP
    if LOOP:
        LOOP = False
        await send_embed(ctx, "Playlist unlooped", 40)


@client.command(name="remove", help="Removes a specified song from the queue", aliases=["eliminar", "sacar", "borrar"])
async def remove(ctx, index: int):
    global QUEUE, INDEX
    if INDEX <= index < len(QUEUE):
        await send_embed(ctx, f" '{QUEUE[index][0]}' has been removed from the queue", 60)
        QUEUE.pop(index)
    elif index == "":
        await send_embed(ctx, "Please indicate what song to delete from the queue", 40)
    else:
        await send_embed(ctx, "Invalid number", 40)


@client.command(name="Cq", help="Clears the queue", aliases=["clear"])
async def cq(ctx):
    global QUEUE, INDEX
    if len(QUEUE) > 0:
        QUEUE = []
        INDEX = 0
        await pause(ctx)
        await send_embed(ctx, "The queue has been cleared", 40)


# -----------------------------------------------Random---------------------------------------------------#

@client.command(name="random", help="Plays a random song from spotify", aliases=["rand", "azar"])
async def random(ctx, amount: int = 1):
    for n in range(0, amount):
        song_list = randMusic()
        try:
            choice = ran.choice(song_list)
        except TypeError:
            await random(ctx)
        else:
            await p(ctx, args=choice)


def randWord(lan):
    if lan in first_df.columns:
        rand1 = first_df[lan].loc[ran.randint(0, first_df.shape[0])]
        if rand1 == "Choose again":
            randWord(lan)
        elif type(rand1) == str:
            choice = ran.randint(0, 9)
            if choice <= 1:
                rand1 += ran.choice(All)
            return rand1
    elif lan in second_df.columns:
        rand2 = second_df[lan].loc[ran.randint(0, second_df.shape[0])]
        if rand2 == "Choose again":
            randWord(lan)
        elif type(rand2) == str:
            choice = ran.randint(0, 9)
            if choice <= 1:
                rand2 += ran.choice(All)
            return rand2


def randSent():
    TRACK_l = []
    TRACK = ""
    choice = ran.randint(0, 9)
    if choice >= 2:
        lan = ran.choice([*first_df.columns, *second_df.columns])
        for n in range(0, ran.randint(1, 4)):
            part = randWord(lan)
            if part != "Choose again" and type(part) == str:
                TRACK += part + " "
                TRACK_l.append(TRACK)

        if type(TRACK_l) == list and len(TRACK_l) == 0:
            randSent()
        elif type(TRACK_l) == list and len(TRACK_l) >= 1:
            return TRACK_l
        elif TRACK_l is None:
            randSent()

    elif choice <= 1:
        for i in range(0, 10):
            TRACK += ran.choice(All)
            TRACK_l.append(TRACK)

        return TRACK_l


def randMusic():
    song_list1 = randSent()
    song_list_f = []
    if type(song_list1) == list and len(song_list1) > 0:
        for item in song_list1:
            try:
                song = Client.search(type="track", q=item, limit=1)
                if len(song["tracks"]["items"]) > 0:
                    song = song["tracks"]["items"][0]["external_urls"]["spotify"]
                    song_list_f.append(song)
            except spotipy.exceptions.SpotifyException or HTTPError or TypeError:
                refresh()
                randMusic()

        if type(song_list_f) == list and len(song_list_f) >= 1:
            return song_list_f
        elif type(song_list_f) == list and len(song_list_f) < 1:
            randMusic()
        elif song_list_f is None:
            randMusic()
    else:
        randMusic()


# --------------------------------------------------------------------------------------------------------------------#


# -------------------------------- Other CMD's ----------------------------------#


@client.command(name="haceme_un_sanguche", help="Para bauti", aliases=["sanguchito"])
async def haceme_un_sanguche(ctx):
    await REDDIT(ctx, ["sandwich", "Sandwich", "sandwiches", "sandwiches", "Thighs"])


@client.command(name="boca", help="Dale boca dale", aliases=["dale_boca"])
async def boca(ctx):
    try:
        await p(ctx, args="https://www.youtube.com/watch?v=jrzOn0Uz15g&ab_channel=Niglett")
    except spotipy.exceptions.SpotifyException or HTTPError or TypeError:
        refresh()
        await boca(ctx)
    else:
        await send_embed(ctx, "Vamos boca :blue_heart::yellow_heart::blue_heart:", 60)


@client.command(name="nene_malo", help="Lo bailan las rochas tambien las chetas", aliases=["rochas", "chetas"])
async def nene_malo(ctx):
    try:
        await p(ctx, args="https://open.spotify.com/track/3lC4mM6NiSLttfYTv1HTNQ?si=973671fd69054a13")
    except spotipy.exceptions.SpotifyException or HTTPError or TypeError:
        refresh()
        await nene_malo(ctx)
    else:
        await send_embed(ctx, "Lo bailan las rochas tambien las chetas", 60)


# -----------------------------------------------NSFW---------------------------------------------------------#
@client.command(name="traps", help="NSFW Traps", aliases=["trapito", "trapitos"])
async def traps(ctx):
    if ctx.message.channel.is_nsfw() is True:
        await REDDIT(ctx, ["traps", "trapsgonewild", "trapsexuals"])
    else:
        await send_embed(ctx, "This channel doesn't support NSFW", None)


@client.command(name="porn", help="NSFW Lechoso el que lo use", aliases=["porno", "paja"])
async def porn(ctx):
    if ctx.message.channel.is_nsfw() is True:
        await REDDIT(ctx, ["porn", "Porn", "porngifs"])
    else:
        await send_embed(ctx, "This channel doesn't support NSFW", None)


@client.command(name="gay", help="NSFW Gay", aliases=["trolo", "putos"])
async def gay(ctx):
    if ctx.message.channel.is_nsfw() is True:
        await REDDIT(ctx, ["gayporn", "GaybrosGoneWild"])
    else:
        await send_embed(ctx, "This channel doesn't support NSFW", None)

@client.command(name="boobs", help="NSFW Boobs", aliases=["tetas", "teta", "tittie"])
async def boobs(ctx):
    if ctx.message.channel.is_nsfw() is True:
        await REDDIT(ctx, ["boob", "boobbounce", "boobs", "Boobies"])
    else:
        await send_embed(ctx, "This channel doesn't support NSFW", None)


@client.command(name="Porn4k", help="NSFW  Para los mas lechosos", aliases=["4k", "4kP"])
async def Porn4k(ctx):
    if ctx.message.channel.is_nsfw() is True:
        await REDDIT(ctx, ["4kPorn", "4k_porn"])
    else:
        await send_embed(ctx, "This channel doesn't support NSFW", None)


@client.command(name="ass", help="NSFW ass", aliases=["culo", "culos", "booty"])
async def ass(ctx):
    if ctx.message.channel.is_nsfw() is True:
        await REDDIT(ctx, ["ass", "booty", "booty_queens"])
    else:
        await send_embed(ctx, "This channel doesn't support NSFW", None)


@client.command(name="r_search", help="Search reddit images (CaSe SenSitiVe)", aliases=["search", "reddit", "rsearch"])
async def r_search(ctx, *, args):
    search = args
    subreddit = await reddit.subreddit(search)
    try:
        je = []
        async for si in subreddit.hot(limit=25):
            je.append(si.url)
    except asyncprawcore.exceptions.Forbidden:
        await send_embed(ctx, "Subreddit private", 40)
    except asyncprawcore.exceptions.Redirect:
        await send_embed(ctx, "Subreddit not found ", 40)
    except asyncprawcore.exceptions.NotFound:
        await send_embed(ctx, "Subreddit is banned", 40)
    else:
        if len(je) < 25:
            await send_embed(ctx, "The subreddit has very few posts", 40)
        else:
            await REDDIT(ctx, [subreddit])


# -----------------------------------------------NSFW---------------------------------------------------------#
async def REDDIT(ctx, choices: list):
    if choices == [0, 1]:
        subr = ran.choice(choices)
        if subr == 1:
            subreddit = await reddit.random_subreddit(nsfw=True)
        else:
            subreddit = await reddit.random_subreddit()
    elif len(choices) == 1:
        subreddit = choices[0]
    else:
        subr = ran.choice(choices)
        subreddit = await reddit.subreddit(subr)

    submission = await subreddit.random()

    if submission is not None:
        if "png" in submission.url[-4:] or "jpg" in submission.url[-4:] or "jpge" in submission.url[
                                                                                     -4:] or "gif" in submission.url[
                                                                                                      -4:] \
                and "gifv" not in submission.url[-5:]:
            embed = Embed(color=discord.Colour.orange())
            embed.set_author(name=subreddit.display_name, url=f"https://www.reddit.com/r/{subreddit.display_name}/")
            embed.set_image(url=submission.url)

            if choices == ["sandwich", "Sandwich", "sandwiches", "sandwiches", "Thighs"]:
                embed.set_footer(text=f"Aqui tienes tu sandwich '{ctx.message.author.name}' uwu",
                                 icon_url=ctx.message.author.avatar_url)
            else:
                embed.set_footer(text=ctx.message.author.name,
                                 icon_url=ctx.message.author.avatar_url)

            await ctx.send(embed=embed)
        else:
            await REDDIT(ctx, choices)
    else:
        await REDDIT(ctx, choices)


@client.command(name="random_subr", help="Random Subreddit", aliases=["rand_subr", "randr", "rsubr"])
async def random_subr(ctx):
    await REDDIT(ctx, [0, 1])


@client.command(name="help", help="This command", aliases=["ayuda"])
async def help(ctx, help_type: str = " "):
    embed = Embed(color=discord.Colour.orange())
    embed.set_author(name=f"Help {help_type.title()}")
    if help_type == " ":
        embed.add_field(name="Music", value="Help with music\nExamples = play, queue, skip",
                        inline=True)
        embed.add_field(name="NSFW", value="Help with NSFW\nExamples = porn, 4kPorn, traps",
                        inline=True)
        embed.add_field(name="Extras", value="Help with extras\nExamples = random, ping, reddit search",
                        inline=True)
    elif help_type.casefold() == "music":
        for command in client.commands:
            if command.name in ["p", "back", "stop", "leave", "q", "loop", "unloop",
                                "remove", "Cq", "pause", "resume", "skip"]:
                embed.add_field(name=f"{command.name}",
                                value=f"{command.help}.\nAlso works with = {str(command.aliases)}",
                                inline=True)
    elif help_type.casefold() == "nsfw":
        for command in client.commands:
            if command.name in ["porn", "gay", "boobs", "Porn4k", "traps", "ass"]:
                embed.add_field(name=f"{command.name}",
                                value=f"{command.help}.\nAlso works with = {str(command.aliases)}",
                                inline=True)
    elif help_type.casefold() == "extras":
        for command in client.commands:
            if command.name in ["help", "random", "haceme_un_sanguche",
                                "nene_malo", "boca", "ping", "r_search", "random_subr"]:
                embed.add_field(name=f"{command.name}",
                                value=f"{command.help}.\nAlso works with = {str(command.aliases)}",
                                inline=True)
    else:
        embed.set_author(name="Invalid help command")

    await ctx.send(embed=embed)


# -------------------------------------------------PROJECTS-----------------------------------------------------------#
# @client.command(name="fiesta", help="Fiestita")
# async def fiesta(ctx):

async def load_subredits():
    global s_list
    subreddit = await reddit.subreddit("sandwich")
    for n in range(0, 500):
        submission = await subreddit.random()
        if ("png" or "jpg" or "jpge" or "gif") in submission.url[-5:]:
            s_list.append(submission.url)
    print(s_list)
# ---------------------------------------------------------------------------------------------------------------------#
client.run(key)
