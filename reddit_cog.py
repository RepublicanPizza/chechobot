import asyncprawcore
import discord
from discord import Embed
from discord.ext import commands
import random as ran
import os
import asyncpraw


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.Reddit_id = os.environ["Reddit_id"]
        self.Reddit_secret = os.environ["Reddit_secret"]
        self.Reddit_agent = os.environ["Reddit_agent"]

        self.reddit = asyncpraw.Reddit(client_id=self.Reddit_id, client_secret=self.Reddit_secret,
                                       user_agent=self.Reddit_agent)

    @commands.command(name="haceme_un_sanguche", help="Para bauti", aliases=["sanguchito"])
    async def haceme_un_sanguche(self, ctx):
        await self.REDDIT(ctx, ["sandwich", "Sandwich", "sandwiches", "sandwiches", "Thighs"])

# -----------------------------------------------NSFW---------------------------------------------------------#
    @commands.command(name="traps", help="NSFW Traps", aliases=["trapito", "trapitos"])
    async def traps(self, ctx):
        if ctx.message.channel.is_nsfw() is True:
            await self.REDDIT(ctx, ["traps", "trapsgonewild", "trapsexuals"])
        else:
            await self.send_embed(ctx, "This channel doesn't support NSFW", None)

    @commands.command(name="porn", help="NSFW Lechoso el que lo use", aliases=["porno", "paja"])
    async def porn(self, ctx):
        if ctx.message.channel.is_nsfw() is True:
            await self.REDDIT(ctx, ["porn", "Porn", "porngifs"])
        else:
            await self.send_embed(ctx, "This channel doesn't support NSFW", None)

    @commands.command(name="gay", help="NSFW Gay", aliases=["trolo", "putos"])
    async def gay(self, ctx):
        if ctx.message.channel.is_nsfw() is True:
            await self.REDDIT(ctx, ["gayporn", "GaybrosGoneWild"])
        else:
            await self.send_embed(ctx, "This channel doesn't support NSFW", None)

    @commands.command(name="boobs", help="NSFW Boobs", aliases=["tetas", "teta", "tittie"])
    async def boobs(self, ctx):
        if ctx.message.channel.is_nsfw() is True:
            await self.REDDIT(ctx, ["boob", "boobbounce", "boobs", "Boobies"])
        else:
            await self.send_embed(ctx, "This channel doesn't support NSFW", None)

    @commands.command(name="Porn4k", help="NSFW  Para los mas lechosos", aliases=["4k", "4kP"])
    async def Porn4k(self, ctx):
        if ctx.message.channel.is_nsfw() is True:
            await self.REDDIT(ctx, ["4kPorn", "4k_porn"])
        else:
            await self.send_embed(ctx, "This channel doesn't support NSFW", None)

    @commands.command(name="ass", help="NSFW ass", aliases=["culo", "culos", "booty"])
    async def ass(self, ctx):
        if ctx.message.channel.is_nsfw() is True:
            await self.REDDIT(ctx, ["ass", "booty", "booty_queens"])
        else:
            await self.send_embed(ctx, "This channel doesn't support NSFW", None)

    @commands.command(name="r_search", help="Search reddit images (CaSe SenSitiVe)",
                      aliases=["search", "reddit", "rsearch"])
    async def r_search(self, ctx, *, args):
        search = args
        subreddit = await self.reddit.subreddit(search)
        try:
            je = []
            async for si in subreddit.hot(limit=25):
                je.append(si.url)
        except asyncprawcore.exceptions.Forbidden:
            await self.send_embed(ctx, "Subreddit private", 40)
        except asyncprawcore.exceptions.Redirect:
            await self.send_embed(ctx, "Subreddit not found ", 40)
        except asyncprawcore.exceptions.NotFound:
            await self.send_embed(ctx, "Subreddit is banned", 40)
        else:
            if len(je) < 25:
                await self.send_embed(ctx, "The subreddit has very few posts", 40)
            else:
                await self.REDDIT(ctx, [subreddit])

# -----------------------------------------------Base command---------------------------------------------------------#
    async def REDDIT(self, ctx, choices: list):
        if choices == [0, 1]:
            subr = ran.choice(choices)
            if subr == 1:
                subreddit = await self.reddit.random_subreddit(nsfw=True)
            else:
                subreddit = await self.reddit.random_subreddit()
        elif len(choices) == 1:
            subreddit = choices[0]
        else:
            subr = ran.choice(choices)
            subreddit = await self.reddit.subreddit(subr)

        submission = await subreddit.random()

        if submission is not None:
            if "png" in submission.url[-4:] \
                    or "jpg" in submission.url[-4:] \
                    or "jpge" in submission.url[-4:] \
                    or "gif" in submission.url[-4:] \
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
                await self.REDDIT(ctx, choices)
        else:
            await self.REDDIT(ctx, choices)

    @commands.command(name="random_subr", help="Random Subreddit", aliases=["rand_subr", "randr", "rsubr"])
    async def random_subr(self, ctx):
        await self.REDDIT(ctx, [0, 1])

    async def send_embed(self, ctx, author: str, delete: int = None):
        embed = Embed(color=discord.Colour.orange())
        embed.set_author(name=author)
        await ctx.send(embed=embed, delete_after=delete)


# -------------------------------------------------PROJECTS-----------------------------------------------------------#
# @client.command(name="fiesta", help="Fiestita")
# async def fiesta(ctx):

#async def load_subredits():
#    global s_list
#    subreddit = await reddit.subreddit("sandwich")
        #    for n in range(0, 500):
        #submission = await subreddit.random()
        #if ("png" or "jpg" or "jpge" or "gif") in submission.url[-5:]:
    #    s_list.append(submission.url)
    #print(s_list)
