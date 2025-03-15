from discord import app_commands
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv


load_dotenv()
from utils.Module import ModuleCheck
from utils.emojis import *

from utils.HelpEmbeds import (
    BotNotConfigured,
    NoPermissionChannel,
    ChannelNotFound,
    ModuleNotEnabled,
    NoChannelSet,
    Support,
    ModuleNotSetup,
)


class suggestions(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client


    @commands.hybrid_command(description="Submit a suggestion for improvement")
    @app_commands.describe(suggestion="The suggestion to make.")
    async def suggest(
        self,
        ctx: commands.Context,
        *,
        suggestion: discord.ext.commands.Range[str, 1, 1024],
        image: discord.Attachment = None,
    ):
        await ctx.defer(ephemeral=True)
        if self.client.suggestions_maintenance is True:
            await ctx.send(
                f"  **{ctx.author.display_name}**, the suggestion module is currently under maintenance. Please try again later.",
            )
            return

        if not await ModuleCheck(ctx.guild.id, "suggestions"):

            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not image is None:
            if isinstance(image, str):
                image = image
            else:
                image = image.url
        else:
            image = None

        Config = await self.client.config.find_one({"_id": ctx.guild.id})
        if not Config:
            return await ctx.send(embed=BotNotConfigured(), view=Support())

        if not Config.get("Suggestions"):
            return await ctx.send(
                embed=ModuleNotSetup(),
                view=Support(),
            )
        try:
            channel = await ctx.guild.fetch_channel(
                Config.get("Suggestions", {}).get("channel")
            )
        except (discord.NotFound, discord.HTTPException):
            return await ctx.send(
                embed=ChannelNotFound(),
                view=Support(),
            )
        if not channel:
            return await ctx.send(
                embed=NoChannelSet(),
                view=Support(),
            )
        if not channel.permissions_for(ctx.guild.me).send_messages:
            return await ctx.send(
                embed=NoPermissionChannel(channel),
            )
        msg = await ctx.send(
            f"<a:Loading:1167074303905386587>  **{ctx.author.display_name}**, submitting suggestion..."
        )
        result = await self.client.db['suggestions'].insert_one(
            {
                "author_id": ctx.author.id,
                "suggestion": suggestion,
                "image": image,
                "upvotes": 0,
                "downvotes": 0,
                "upvoters": [],
                "downvoters": [],
                "guild_id": ctx.guild.id,
            }
        )
        self.client.dispatch("suggestion", result.inserted_id, Config)
        await msg.edit(
            content=f"  **{ctx.author.display_name},** succesfully submitted suggestion."
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(suggestions(client))
