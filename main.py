import discord
from discord import Embed
from discord.ext import commands
import os
from music_cog import Music
from reddit_cog import Reddit

key = os.environ["DISCORD"]

client = commands.Bot(command_prefix=".")
client.remove_command("help")
client.add_cog(Music(client))
client.add_cog(Reddit(client))


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game("Listening to .help"))


@client.command(name="ping", help="Shows the bot's latency", aliases=["Ping"])
async def ping(ctx):
    await send_embed(ctx, f"Pong! {round(client.latency * 1000)}ms", 40)


async def send_embed(ctx, author: str, delete: int = None):
    embed = Embed(color=discord.Colour.orange())
    embed.set_author(name=author)
    await ctx.send(embed=embed, delete_after=delete)


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


client.run(key)
