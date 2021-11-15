import discord
from aiohttp import ClientError
from discord.errors import ClientException, NotFound
from discord.ext import commands, tasks
from youtube_dl import YoutubeDL
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import random as ran
import os

# -------------------------------- Parameters ----------------------------------#
PLAYLIST = False
INDEX = 0
QUEUE = []
ID = 0
playing = False
LOOP = False
key = os.environ["DISCORD"]
first_df = pd.read_csv("to-ZETW.csv", dtype="unicode")
second_df = pd.read_csv("AF-to-IT.csv", dtype="unicode")
All = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '!', '#', '$', '%', '&', '(', ')', '+', '/', ":"]

# -------------------------------- Spotify ---------------------------------#
CLIENT_ID = os.environ["SPOTIFY-ID"]
CLIENT_SECRET = os.environ["SPOTIFY-SECRET"]
REDIRECT = "http://example.com"
SCOPE = "playlist-read-private"

credentials = spotipy.oauth2.SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

authorization = spotipy.oauth2.SpotifyOAuth(client_id=credentials.client_id, client_secret=credentials.client_secret,
                                            redirect_uri=REDIRECT, cache_path=".cache", scope=SCOPE)

# authorization.get_access_token(code=authorization.get_authorization_code())
token = authorization.get_cached_token()["access_token"]

Client = spotipy.client.Spotify(auth=token,
                                client_credentials_manager=credentials,
                                oauth_manager=authorization, auth_manager=authorization.cache_handler)


def refresh():
    global token, authorization

    if authorization.is_token_expired(authorization.get_cached_token()):
        token_info = authorization.refresh_access_token(authorization.get_cached_token()['refresh_token'])
        token = token_info["access_token"]


def getTracks(url):
    global PLAYLIST, QUEUE
    if "www.youtube.com" in url:
        PLAYLIST = False
        url = url[32:43]
        youtube_op = {"format": "bestaudio", "noplaylist": "True"}
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
    elif "open.spotify.com/playlist" in url:
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
    elif "open.spotify.com/album" in url:
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
    else:
        PLAYLIST = False
        youtube_op = {"format": "bestaudio", "noplaylist": "True"}
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


@client.command(name="ping", help="Shows the bot's latency")
async def ping(ctx):
    await ctx.send(f"Pong! {round(client.latency * 1000)}ms")


# -------------------------------- Play CMD ----------------------------------#

@client.command(name="p", help="Searches and plays the song by title or YT url or Spotify Url")
async def p(ctx, title):
    global playing, INDEX, PLAYLIST, QUEUE
    if not playing:
        try:
            user = ctx.message.author
            vc = user.voice.channel
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        except AttributeError:
            await ctx.send("You must be connected to a voice channel first")
        else:
            if voice is None:
                await vc.connect()
                refresh()
                getTracks(title)
                await play_music(ctx)
            elif voice.channel and voice.channel == vc:
                refresh()
                getTracks(title)
                await play_music(ctx)
    else:
        user = ctx.message.author
        vc = user.voice.channel
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if voice.channel != vc:
            await ctx.send("Already playing on another channel")
        elif voice.channel == vc and not PLAYLIST:
            refresh()
            getTracks(title)
            item = len(QUEUE) - 1
            embed = discord.Embed(color=discord.Colour.orange())
            embed.set_author(name=f" '{QUEUE[item][0]}' added to queue")
            await ctx.send(embed=embed, delete_after=60)
        elif voice.channel == vc and PLAYLIST:
            refresh()
            getTracks(title)
            embed = discord.Embed(color=discord.Colour.orange())
            embed.set_author(name="Playlist added to queue")
            await ctx.send(embed=embed, delete_after=60)


async def play_music(ctx):
    global INDEX, ID
    embed = discord.Embed(color=discord.Color.orange())
    play_next(ctx)
    embed.set_author(name=f"Currently playing: {QUEUE[INDEX - 1][0]}")
    after = After(QUEUE[INDEX - 1][1]) + 5
    message = await ctx.send(embed=embed, delete_after=after)
    ID = message.id


def play_next(ctx):
    global playing, INDEX, QUEUE, LOOP
    refresh()
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
        elif len(QUEUE[INDEX]) == 2:
            url = downloadSpoti(INDEX)
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
            voice.play(source=discord.FFmpegPCMAudio(url, **ff_op), after=lambda e: play_next(ctx))
            save(QUEUE[INDEX][0])
            playing = True
            INDEX += 1
    else:
        playing = False


def downloadSpoti(INDEX):
    global QUEUE
    youtube_op = {"format": "bestaudio", "noplaylist": "True"}
    with YoutubeDL(youtube_op) as yt:
        try:
            info = yt.extract_info("ytsearch:%s" % f"{QUEUE[INDEX][0]}", download=False)["entries"][0]
            url = info["formats"][0]["url"]
        except Exception:
            None
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
        embed = discord.Embed(color=discord.Color.orange())
        embed.set_author(name=f"Currently playing: {QUEUE[INDEX - 1][0]}")
        after = After(QUEUE[INDEX - 1][1])
        message = await message.channel.send(embed=embed, delete_after=after)
        ID = message.id


@client.command(name="pause", help="Pauses the current song")
async def pause(ctx):
    global playing
    if playing:
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        voice.pause()
        playing = False


@client.command(name="resume", help="Resumes the current song")
async def resume(ctx):
    global playing
    if not playing:
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        voice.resume()
        playing = True


@client.command(name="skip", help="Skips the current song (the amount of songs to skip can be specified)")
async def skip(ctx, amount: int = 1):
    global playing, INDEX, ID
    if playing:
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        voice.pause()
        message = await ctx.fetch_message(id=ID)
        INDEX += amount - 1
        play_next(ctx)
        await message.delete(delay=None)


@client.command(name="back", help="Goes back to the last song played")
async def back(ctx):
    global INDEX
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if playing and INDEX > 1:
        voice.pause()
        INDEX -= 2
        try:
            message = await ctx.fetch_message(id=ID)
        except NotFound:
            None
        else:
            await message.delete(delay=None)
        play_next(ctx)
    elif playing and INDEX == 1:
        voice.pause()
        INDEX -= 1
        try:
            message = await ctx.fetch_message(id=ID)
        except NotFound:
            None
        else:
            await message.delete(delay=None)
        play_next(ctx)


@client.command(name="stop", help="Stops the current song(clears the queue)")
async def stop(ctx):
    global ID
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.pause()
    try:
        message = await ctx.fetch_message(id=ID)
    except NotFound:
        None
    else:
        resetVariables()
        await message.delete(delay=None)
    embed = discord.Embed(color=discord.Colour.orange())
    embed.set_author(name="Stoped playing music")
    await ctx.send(embed=embed, delete_after=20)


@client.command(name="leave", help="Leaves the current voice channel")
async def leave(ctx):
    global playing, INDEX
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice is not None:
        voice.stop()
        await voice.disconnect()
        try:
            message = await ctx.fetch_message(id=ID)
        except NotFound:
            None
        else:
            await message.delete(delay=None)
        resetVariables()
    elif voice is None:
        embed = discord.Embed(color=discord.Colour.orange())
        embed.set_author(name="Can't use that command right now")
        await ctx.send(embed=embed, delete_after=20)


@client.command(name="q", help="Shows the queue")
async def q(ctx):
    global QUEUE, INDEX
    embed = discord.Embed(color=discord.Colour.orange())
    embed.set_author(name="Queue")
    if len(QUEUE) > 0:
        for i in range(0, len(QUEUE)):
            if i == INDEX - 1:
                embed.add_field(name="Current", value=f" '{QUEUE[i][0]}' Duration: {QUEUE[i][1]}", inline=True)
            else:
                embed.add_field(name=f"{i}", value=f" '{QUEUE[i][0]}' Duration: {QUEUE[i][1]}", inline=True)
        await ctx.send(embed=embed, delete_after=60)
    else:
        embed = discord.Embed(color=discord.Colour.orange())
        embed.set_author(name="No music in the queue")
        await ctx.send(embed=embed, delete_after=20)


def resetVariables():
    global PLAYLIST, INDEX, QUEUE, ID, playing, LOOP
    PLAYLIST = False
    INDEX = 0
    QUEUE = []
    ID = 0
    playing = False
    LOOP = False


@client.command(name="loop", help="Loops the current queue")
async def loop(ctx):
    global LOOP
    if len(QUEUE) > 0:
        LOOP = True
    await ctx.send("Playlist looped")


@client.command(name="unloop", help="Unloops the current queue")
async def unloop(ctx):
    global LOOP
    if LOOP:
        LOOP = False
    await ctx.send("Playlist unlooped")


@client.command(name="remove", help="Removes a specified song from the queue")
async def remove(ctx, index: int):
    global QUEUE, INDEX
    if INDEX <= index < len(QUEUE):
        embed = discord.Embed(color=discord.Colour.orange())
        embed.set_author(name=f" '{QUEUE[index][0]}' has been removed from the queue")
        QUEUE.pop(index)
        await ctx.send(embed=embed, delete_after=60)
    elif index == "":
        embed = discord.Embed(color=discord.Colour.orange())
        embed.set_author(name="Please indicate what song to delete from the queue")
        await ctx.send(embed=embed, delete_after=20)
    else:
        embed = discord.Embed(color=discord.Colour.orange())
        embed.set_author(name="Invalid number")
        await ctx.send(embed=embed, delete_after=20)


@client.command(name="random", help="Plays a random song from spotify")
async def random(ctx, amount: int = 1):
    for n in range(0, amount):
        song_list = randMusic()
        try:
            choice = ran.choice(song_list)
        except TypeError:
            await random(ctx)
        else:
            await p(ctx, choice)


def randWord(lan):
    if lan in first_df.columns:
        rand1 = first_df[lan].loc[ran.randint(0, first_df.shape[0])]
        if rand1 == "Choose again":
            randWord(lan)
        elif type(rand1) == str:
            choice = ran.randint(0, 9)
            if choice < 2:
                rand1 += ran.choice(All)
            return rand1
    elif lan in second_df.columns:
        rand2 = second_df[lan].loc[ran.randint(0, second_df.shape[0])]
        if rand2 == "Choose again":
            randWord(lan)
        elif type(rand2) == str:
            choice = ran.randint(0, 9)
            if choice < 2:
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

    elif choice < 2:
        for i in range(0, 10):
            TRACK += ran.choice(All)
            TRACK_l.append(TRACK)

        return TRACK_l


def randMusic():
    song_list1 = randSent()
    song_list_f = []
    if type(song_list1) == list and len(song_list1) > 0:
        for item in song_list1:
            song = Client.search(type="track", q=item, limit=1)
            if len(song["tracks"]["items"]) > 0:
                song = song["tracks"]["items"][0]["external_urls"]["spotify"]
                song_list_f.append(song)

        if type(song_list_f) == list and len(song_list_f) >= 1:
            return song_list_f
        elif type(song_list_f) == list and len(song_list_f) < 1:
            randMusic()
        elif song_list_f is None:
            randMusic()
    else:
        randMusic()


@client.command(name="Cq", help="Clears the queue")
async def cq(ctx):
    global QUEUE, INDEX, playing
    if len(QUEUE) > 0:
        QUEUE = []
        INDEX = 0
        await pause(ctx)
        embed = discord.Embed(color=discord.Colour.orange())
        embed.set_author(name="The queue has been cleared")
        await ctx.send(embed=embed, delete_after=20)


# -------------------------------- Other CMD's ----------------------------------#

@client.command(name="haceme_un_sanguche", help="Para bauti")
async def haceme_un_sanguche(ctx):
    await ctx.send("Aqui tienes tu sandwich uwu :point_right::point_left:")


@client.command(name="boca", help="Dale boca dale")
async def boca(ctx):
    await p(ctx, "https://www.youtube.com/watch?v=jrzOn0Uz15g&ab_channel=Niglett")
    await ctx.send("Vamos boca :blue_heart::yellow_heart::blue_heart:")


@client.command(name="help", help="This command")
async def help(ctx):
    embed = discord.Embed(color=discord.Colour.orange())
    embed.set_author(name="Help")

    for command in client.commands:
        embed.add_field(name=f"{command.name}", value=f"{command.help}", inline=False)

    await ctx.send(embed=embed, delete_after=100)


client.run(key)
