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


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.PLAYLIST = False
        self.INDEX = 0
        self.QUEUE = []
        self.ID = 0
        self.playing = False
        self.LOOP = False
        self.TIME = 0
        self.key = os.environ["DISCORD"]
        self.first_df = pd.read_csv("to-ZETW.csv", dtype="unicode")
        self.second_df = pd.read_csv("AF-to-IT.csv", dtype="unicode")
        self.All = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '!', '#', '$', '%', '&', '(', ')', '+', '/', ":"]
        self.youtube_op = {"format": "bestaudio", "noplaylist": "True", "--age-limit": 25}
        self.ff_op = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", "options": "-vn"}

        # -------------------------------- Spotify  ---------------------------------#
        self.CLIENT_ID = os.environ["SPOTIFY-ID"]
        self.CLIENT_SECRET = os.environ["SPOTIFY-SECRET"]
        self.REDIRECT = "http://example.com"
        self.SCOPE = "playlist-read-private"

        self.credentials = spotipy.oauth2.SpotifyClientCredentials(client_id=self.CLIENT_ID,
                                                                   client_secret=self.CLIENT_SECRET)

        self.authorization = SpotifyOAuth(client_id=self.credentials.client_id,
                                          client_secret=self.credentials.client_secret,
                                          redirect_uri=self.REDIRECT, cache_path=".cache", scope=self.SCOPE)

        self.Client = spotipy.client.Spotify(auth=self.authorization.get_cached_token()["access_token"],
                                             requests_timeout=10, retries=10)

    def refresh(self):

        token_info = self.authorization.refresh_access_token(self.authorization.get_cached_token()['refresh_token'])
        token = token_info["access_token"]
        self.Client = spotipy.client.Spotify(auth=token, requests_timeout=10, retries=10)

    def getTracks(self, url):
        if "www.youtube.com" in url:
            self.PLAYLIST = False
            with YoutubeDL(self.youtube_op) as yt:
                try:
                    info = yt.extract_info("ytsearch:%s" % f"{url}", download=False)["entries"][0]
                except Exception:
                    print("Error")
                else:
                    url = info["formats"][0]["url"]
                    title = info["title"]
                    duration = info["duration"]
                    time = self.sec_a_MinSec(duration)
                    self.QUEUE.append([title, time, url])
        elif "open.spotify.com/track" in url:
            try:
                self.PLAYLIST = False
                search = self.Client.track(f"{url}")
                TRACK_TIME = self.mils_to_MinSec(search["duration_ms"])
                TRACK_ARTIST = search["artists"]
                if len(TRACK_ARTIST) > 0:
                    TRACK_ARTIST = TRACK_ARTIST[0]["name"]
                elif len(TRACK_ARTIST) == 0:
                    TRACK_ARTIST = search["artists"]["name"]
                TRACK_NAME = search["name"]
                TRACK = TRACK_ARTIST + " " + TRACK_NAME
                self.QUEUE.append([TRACK, TRACK_TIME])

            except spotipy.exceptions.SpotifyException or HTTPError or TypeError:
                self.refresh()
                self.getTracks(url)

        elif "open.spotify.com/playlist" in url:
            try:
                self.PLAYLIST = True
                search = self.Client.playlist_tracks(f"{url}")
                for n in range(0, len(search["items"])):
                    TRACK_ARTIST = search["items"][n]["track"]["artists"]
                    if len(TRACK_ARTIST) > 0:
                        TRACK_ARTIST = TRACK_ARTIST[0]["name"]
                    else:
                        TRACK_ARTIST = search["items"][n]["track"]["artists"]["name"]
                    TRACK_NAME = search["items"][n]["track"]["name"]
                    TRACK_TIME = self.mils_to_MinSec(search["items"][n]["track"]["duration_ms"])
                    TRACK = TRACK_ARTIST + " " + TRACK_NAME
                    self.QUEUE.append([TRACK, TRACK_TIME])

            except spotipy.exceptions.SpotifyException or HTTPError or TypeError:
                self.refresh()
                self.getTracks(url)

        elif "open.spotify.com/album" in url:
            try:
                self.PLAYLIST = True
                search = self.Client.album_tracks(f"{url}")
                for n in range(0, len(search["items"])):
                    TRACK_ARTIST = search["items"][n]["artists"]
                    if len(TRACK_ARTIST) > 0:
                        TRACK_ARTIST = TRACK_ARTIST[0]["name"]
                    else:
                        TRACK_ARTIST = search["items"][n]["artists"]["name"]
                    TRACK_NAME = search["items"][n]["name"]
                    TRACK = TRACK_ARTIST + " " + TRACK_NAME
                    TRACK_TIME = self.mils_to_MinSec(search["items"][n]["duration_ms"])
                    self.QUEUE.append([TRACK, TRACK_TIME])

            except spotipy.exceptions.SpotifyException or HTTPError or TypeError:
                self.refresh()
                self.getTracks(url)
        else:
            self.PLAYLIST = False
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
                    time = self.sec_a_MinSec(duration)
                    self.QUEUE.append([title, time, url])

    def mils_to_MinSec(self, tem):
        time_ms = int(tem) // 1000
        time_min = time_ms // 60
        time_sec = time_ms % 60
        if time_sec < 10:
            TRACK_TIME = f"{time_min}:0{time_sec}"
        else:
            TRACK_TIME = f"{time_min}:{time_sec}"
        return TRACK_TIME

    def sec_a_MinSec(self, tem):
        min = int(tem) // 60
        sec = int(tem) % 60
        if sec < 10:
            duration = f"{min}:0{sec}"
        else:
            duration = f"{min}:{sec}"
        return duration

    def save(self, song):
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

    async def send_embed(self, ctx, author: str, delete: int = None):
        embed = Embed(color=discord.Colour.orange())
        embed.set_author(name=author)
        await ctx.send(embed=embed, delete_after=delete)

# -------------------------------- Play CMD ----------------------------------#

    @commands.command(name="p", help="Searches and plays the song by title or YT url or Spotify Url",
                    aliases=["pone", "play"])
    async def p(self, ctx, *, args):
        if not self.playing:
            try:
                user = ctx.message.author
                vc = user.voice.channel
                voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            except AttributeError:
                await self.send_embed(ctx, "You must be connected to a voice channel first", 40)
            else:
                if voice is None:
                    await vc.connect()
                    self.getTracks(args)
                    await self.play_music(ctx)
                elif voice.channel and voice.channel == vc:
                    self.getTracks(args)
                    await self.play_music(ctx)
        else:
            user = ctx.message.author
            vc = user.voice.channel
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice.channel != vc:
                await self.send_embed(ctx, "Already playing on another channel", 40)
            elif voice.channel == vc and not self.PLAYLIST:
                self.getTracks(args)
                item = len(self.QUEUE) - 1
                await self.send_embed(ctx, f" '{self.QUEUE[item][0]}' added to queue", 120)
            elif voice.channel == vc and self.PLAYLIST:
                self.getTracks(args)
                await self.send_embed(ctx, "Playlist added to queue", 120)

    async def play_music(self, ctx):
        embed = Embed(color=discord.Color.orange())
        self.play_next(ctx)
        embed.set_author(name=f"Currently playing: {self.QUEUE[self.INDEX - 1][0]}")
        after = self.After(self.QUEUE[self.INDEX - 1][1]) + 10
        message = await ctx.send(embed=embed, delete_after=after)
        self.ID = message.id

    def play_next(self, ctx):
        if self.INDEX == len(self.QUEUE) and self.LOOP:
            self.INDEX = 0

        if len(self.QUEUE) > self.INDEX:

            if len(self.QUEUE[self.INDEX]) == 3:
                url = self.QUEUE[self.INDEX][2]
                voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
                voice.play(source=discord.FFmpegPCMAudio(url, **self.ff_op), after=lambda e: self.play_next(ctx))
                self.save(self.QUEUE[self.INDEX][0])
                self.playing = True
                self.INDEX += 1
                self.TIME = time.time()
            elif len(self.QUEUE[self.INDEX]) == 2:
                url = self.downloadSpoti(self.INDEX)
                voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
                voice.play(source=discord.FFmpegPCMAudio(url, **self.ff_op), after=lambda e: self.play_next(ctx))
                self.save(self.QUEUE[self.INDEX][0])
                self.playing = True
                self.INDEX += 1
                self.TIME = time.time()
        else:
            self.playing = False

    def downloadSpoti(self, INDEX):
        with YoutubeDL(self.youtube_op) as yt:
            try:
                info = yt.extract_info("ytsearch:%s" % f"{self.QUEUE[INDEX][0]}", download=False)["entries"][0]
                url = info["formats"][0]["url"]
            except Exception:
                print(None)
            else:
                return url

    def After(self, time):
        sec = int(time[len(time) - 2:])
        min = int(time[0:time.find(":")])
        return sec + min * 60

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author == self.bot.user and self.playing and message.id == self.ID:
            embed = Embed(color=discord.Color.orange())
            embed.set_author(name=f"Currently playing: {self.QUEUE[self.INDEX - 1][0]}")
            after = self.After(self.QUEUE[self.INDEX - 1][1]) + 10
            message = await message.channel.send(embed=embed, delete_after=after)
            self.ID = message.id

    @commands.command(name="pause", help="Pauses the current song", aliases=["para"])
    async def pause(self, ctx):
        if self.playing:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            voice.pause()
            self.playing = False
            await self.send_embed(ctx, "Music Paused", 40)

    @commands.command(name="resume", help="Resumes the current song", aliases=["segui"])
    async def resume(self, ctx):
        if not self.playing:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            voice.resume()
            self.playing = True
            await self.send_embed(ctx, "Music Resumed", 40)

    @commands.command(name="skip", help="Skips the current song (the amount of songs to skip can be specified)",
                    aliases=["next"])
    async def skip(self, ctx, amount: int = 1):
        if self.playing:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            voice.pause()
            message = await ctx.fetch_message(id=self.ID)
            self.INDEX += amount - 1
            self.play_next(ctx)
            await message.delete(delay=None)

    @commands.command(name="back", help="Goes back to the last song played", aliases=["atras"])
    async def back(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if self.playing and self.INDEX > 1:
            voice.pause()
            self.INDEX -= 2
            try:
                message = await ctx.fetch_message(id=self.ID)
            except NotFound:
                print(None)
            else:
                await message.delete(delay=None)
            self.play_next(ctx)
        elif self.playing and self.INDEX == 1:
            voice.pause()
            self.INDEX -= 1
            try:
                message = await ctx.fetch_message(id=self.ID)
            except NotFound:
                print(None)
            else:
                await message.delete(delay=None)
            self.play_next(ctx)

    @commands.command(name="stop", help="Stops the current song(clears the queue)", aliases=["cortala"])
    async def stop(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice.pause()
        try:
            message = await ctx.fetch_message(id=self.ID)
        except NotFound:
            print(None)
        else:
            self.resetVariables()
            await message.delete(delay=None)
        await self.send_embed(ctx, "Stoped playing music", 40)

    @commands.command(name="leave", help="Leaves the current voice channel", aliases=["sali", "andate", "tomatela"])
    async def leave(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice is not None:
            voice.stop()
            await voice.disconnect()
            try:
                message = await ctx.fetch_message(id=self.ID)
            except NotFound:
                print(None)
            else:
                await message.delete(delay=None)
            self.resetVariables()
        elif voice is None:
            await self.send_embed(ctx, "Can't use that command right now", 40)

    def resetVariables(self):
        self.PLAYLIST = False
        self.INDEX = 0
        self.QUEUE = []
        self.ID = 0
        self.playing = False
        self.LOOP = False

# --------------------------------------------------------------------------------------------------------------------#

    @commands.command(name="q", help="Shows the queue", aliases=["cola"])
    async def q(self, ctx):
        embed = Embed(color=discord.Colour.orange())
        embed.set_author(name="Queue")
        if len(self.QUEUE) > 0:
            for i in range(0, len(self.QUEUE)):
                if i == self.INDEX - 1:
                    embed.add_field(name="Current", value=f" '{self.QUEUE[i][0]}' Duration: {self.QUEUE[i][1]}", inline=True)
                else:
                    embed.add_field(name=f"{i}", value=f" '{self.QUEUE[i][0]}' Duration: {self.QUEUE[i][1]}", inline=True)
            await ctx.send(embed=embed, delete_after=120)
        else:
            await self.send_embed(ctx, "No music in the queue", 40)

    @commands.command(name="loop", help="Loops the current queue", aliases=["loopea"])
    async def loop(self, ctx):
        if len(self.QUEUE) > 0:
            self.LOOP = True
            await self.send_embed(ctx, "Playlist looped", 40)

    @commands.command(name="unloop", help="Unloops the current queue", aliases=["desloopea"])
    async def unloop(self, ctx):
        if self.LOOP:
            self.LOOP = False
            await self.send_embed(ctx, "Playlist unlooped", 40)

    @commands.command(name="remove", help="Removes a specified song from the queue",
                    aliases=["eliminar", "sacar", "borrar"])
    async def remove(self, ctx, index: int):
        if self.INDEX <= index < len(self.QUEUE):
            await self.send_embed(ctx, f" '{self.QUEUE[index][0]}' has been removed from the queue", 60)
            self.QUEUE.pop(index)
        elif index == "":
            await self.send_embed(ctx, "Please indicate what song to delete from the queue", 40)
        else:
            await self.send_embed(ctx, "Invalid number", 40)

    @commands.command(name="Cq", help="Clears the queue", aliases=["clear"])
    async def cq(self, ctx):
        if len(self.QUEUE) > 0:
            self.QUEUE = []
            self.INDEX = 0
            await self.pause(ctx)
            await self.send_embed(ctx, "The queue has been cleared", 40)

# -----------------------------------------------Random---------------------------------------------------#

    @commands.command(name="random", help="Plays a random song from spotify", aliases=["rand", "azar"])
    async def random(self, ctx, amount: int = 1):
        for n in range(0, amount):
            song_list = self.randMusic()
            try:
                choice = ran.choice(song_list)
            except TypeError:
                await self.random(ctx)
            else:
                await self.p(ctx, args=choice)

    def randWord(self, lan):
        if lan in self.first_df.columns:
            rand1 = self.first_df[lan].loc[ran.randint(0, self.first_df.shape[0])]
            if rand1 == "Choose again":
                self.randWord(lan)
            elif type(rand1) == str:
                choice = ran.randint(0, 9)
                if choice <= 1:
                    rand1 += ran.choice(self.All)
                return rand1
        elif lan in self.second_df.columns:
            rand2 = self.second_df[lan].loc[ran.randint(0, self.second_df.shape[0])]
            if rand2 == "Choose again":
                self.randWord(lan)
            elif type(rand2) == str:
                choice = ran.randint(0, 9)
                if choice <= 1:
                    rand2 += ran.choice(self.All)
                return rand2

    def randSent(self):
        TRACK_l = []
        TRACK = ""
        choice = ran.randint(0, 9)
        if choice >= 2:
            lan = ran.choice([*self.first_df.columns, *self.second_df.columns])
            for n in range(0, ran.randint(1, 4)):
                part = self.randWord(lan)
                if part != "Choose again" and type(part) == str:
                    TRACK += part + " "
                    TRACK_l.append(TRACK)

            if type(TRACK_l) == list and len(TRACK_l) == 0:
                self.randSent()
            elif type(TRACK_l) == list and len(TRACK_l) >= 1:
                return TRACK_l
            elif TRACK_l is None:
                self.randSent()

        elif choice <= 1:
            for i in range(0, 10):
                TRACK += ran.choice(self.All)
                TRACK_l.append(TRACK)

            return TRACK_l

    def randMusic(self):
        song_list1 = self.randSent()
        song_list_f = []
        if type(song_list1) == list and len(song_list1) > 0:
            for item in song_list1:
                try:
                    song = self.Client.search(type="track", q=item, limit=1)
                    if len(song["tracks"]["items"]) > 0:
                        song = song["tracks"]["items"][0]["external_urls"]["spotify"]
                        song_list_f.append(song)
                except spotipy.exceptions.SpotifyException or HTTPError or TypeError:
                    self.refresh()
                    self.randMusic()

            if type(song_list_f) == list and len(song_list_f) >= 1:
                return song_list_f
            elif type(song_list_f) == list and len(song_list_f) < 1:
                self.randMusic()
            elif song_list_f is None:
                self.randMusic()
        else:
            self.randMusic()

    @commands.command(name="nene_malo", help="Lo bailan las rochas tambien las chetas", aliases=["rochas", "chetas"])
    async def nene_malo(self, ctx):
        try:
            await self.p(ctx, args="https://open.spotify.com/track/3lC4mM6NiSLttfYTv1HTNQ?si=973671fd69054a13")
        except spotipy.exceptions.SpotifyException or HTTPError or TypeError:
            self.refresh()
            await self.nene_malo(ctx)
        else:
            await self.send_embed(ctx, "Lo bailan las rochas tambien las chetas", 60)

    @commands.command(name="boca", help="Dale boca dale", aliases=["dale_boca"])
    async def boca(self, ctx):
        try:
            await self.p(ctx, args="https://www.youtube.com/watch?v=jrzOn0Uz15g&ab_channel=Niglett")
        except spotipy.exceptions.SpotifyException or HTTPError or TypeError:
            self.refresh()
            await self.boca(ctx)
        else:
            await self.send_embed(ctx, "Vamos boca :blue_heart::yellow_heart::blue_heart:", 60)
