import discord
from discord.ext import commands
from typing import Literal
from utils.emojis import *
from datetime import datetime
import os
from utils.format import PaginatorButtons
from utils.permissions import *
from discord import app_commands
from utils.permissions import check_admin_and_staff

from utils.Module import ModuleCheck
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT")

from utils.HelpEmbeds import (
    BotNotConfigured,
    NoPermissionChannel,
    ChannelNotFound,
    ModuleNotEnabled,
    NoChannelSet,
    Support,
    ModuleNotSetup,
)


class Feedback(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_group(description="Staff Feedback")
    async def feedback(self, ctx: commands.Context):
        pass

    @feedback.command(description="Remove feedback from a staff member")
    @app_commands.describe(id="The ID of the feedback you want to remove.")
    async def remove(self, ctx: commands.Context, id: int):
        if self.client.feedback_maintenance is True:
            await ctx.send(
                f"  **{ctx.author.display_name}**, the feedback module is currently under maintenance. Please try again later.",
            )
            return

        if not await ModuleCheck(ctx.guild.id, "Feedback"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Staff Feedback Permission"):

            return
        result = await self.client.db["feedback"].find_one(
            {"feedbackid": id, "guild_id": ctx.guild.id}
        )
        if result is None:
            await ctx.send(
                f"  **{ctx.author.display_name}**, I couldn't find any feedback with that ID."
            )
            return

        await self.client.db["feedback"].delete_one(
            {"feedbackid": id, "guild_id": ctx.guild.id}
        )
        await ctx.send(
            f"  **{ctx.author.display_name}**, I have removed the feedback.",
        )

    @feedback.command(description="Rate a staff member", name="give")
    @app_commands.describe(
        staff="The staff member you want to rate.",
        rating="The rating you want to give (1-10).",
        feedback="The feedback you want to give.",
    )
    async def feedback2(
        self,
        ctx: commands.Context,
        staff: discord.User,
        rating: Literal[
            "1/10",
            "2/10",
            "3/10",
            "4/10",
            "5/10",
            "6/10",
            "7/10",
            "8/10",
            "9/10",
            "10/10",
        ],
        *,
        feedback: discord.ext.commands.Range[str, 1, 2000],
    ):
        if self.client.feedback_maintenance is True:
            await ctx.send(
                f"  **{ctx.author.display_name}**, the feedback module is currently under maintenance. Please try again later.",
            )
            return
        await ctx.defer(ephemeral=True)
        if not await ctx.guild.fetch_member(ctx.author.id):
            return await ctx.send(
                f"  {ctx.author.display_name}, that user isn't in the server."
            )
        existing_feedback = await self.client.db["feedback"].find_one(
            {"guild_id": ctx.guild.id, "staff": staff.id, "author": ctx.author.id}
        )
        Config = await Configuration.find_one({"_id": ctx.guild.id})
        if not Config:
            return await ctx.send(embed=BotNotConfigured(), view=Support())
        if not Config.get("Feedback"):
            return await ctx.send(
                embed=ModuleNotSetup(),
                view=Support(),
            )

        if staff is None:
            await ctx.send(
                f"  **{ctx.author.display_name}**, please provide a staff member.",
            )
            return
        if not await ModuleCheck(ctx.guild.id, "Feedback"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if staff == ctx.author:
            await ctx.send(
                f"  **{ctx.author.display_name}**, you cannot rate yourself.",
            )
            return

        has_staff_role = await check_admin_and_staff(ctx.guild, staff)

        if not has_staff_role:
            await ctx.send(
                f"  **{ctx.author.display_name}**, you can only rate staff members.",
            )
            return
        if Config.get("Module Options"):
            if (
                Config.get("Module Options", {}).get("multiplefeedback", False) is False
                and existing_feedback
            ):
                await ctx.send(
                    f"  **{ctx.author.display_name},** You have already rated this staff member.",
                )
                return
        else:
            if existing_feedback:
                await ctx.send(
                    f"  **{ctx.author.display_name},** You have already rated this staff member.",
                )
                return
        feedbackid = await self.client.db["feedback"].count_documents({}) + 1
        msg = await ctx.send(
            f"<a:Loading:1167074303905386587>  **{ctx.author.display_name}**, submitting feedback..."
        )

        try:
            channel = await ctx.guild.fetch_channel(
                int(Config.get("Feedback", {}).get("channel", 0))
            )
        except (discord.NotFound, discord.HTTPException):
            return await ctx.send(
                embed=ChannelNotFound(),
            )
        if not channel:
            return await ctx.send(
                embed=NoChannelSet(),
            )
        if not channel.permissions_for(ctx.guild.me).send_messages:
            return await ctx.send(
                embed=NoPermissionChannel(channel),
            )

        try:
            Rating = rating.split("/")[0]
            feedbackdata = {
                "guild_id": ctx.guild.id,
                "rating": Rating,
                "staff": staff.id,
                "author": ctx.author.id,
                "feedback": feedback,
                "date": datetime.now().timestamp(),
                "feedbackid": feedbackid,
            }
            insert = await self.client.db["feedback"].insert_one(feedbackdata)
            self.client.dispatch("feedback", insert.inserted_id, Config)
            await msg.edit(
                content=f"  You've rated **@{staff.display_name}** {rating}!",
            )
        except discord.Forbidden:
            await ctx.send(
                embed=NoPermissionChannel(channel),
                view=Support(),
            )
            return

    @feedback.command(description="View a staff members rating")
    @app_commands.describe(
        staff="The staff to view rating for", scope="The scope of the rating to view"
    )
    async def ratings(
        self,
        ctx: commands.Context,
        staff: discord.Member,
        scope: Literal["global", "server"],
    ):
        if self.client.feedback_maintenance is True:
            await ctx.send(
                f"  **{ctx.author.display_name}**, the feedback module is currently under maintenance. Please try again later.",
            )
            return
        if not await ModuleCheck(ctx.guild.id, "Feedback"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return

        if scope == "global":
            staff_ratings = (
                await self.client.db["feedback"]
                .find({"staff": staff.id})
                .to_list(length=None)
            )
            total_ratings = await self.client.db["feedback"].count_documents(
                {"staff": staff.id}
            )
        elif scope == "server":
            staff_ratings = (
                await self.client.db["feedback"]
                .find({"guild_id": ctx.guild.id, "staff": staff.id})
                .to_list(length=None)
            )
            total_ratings = await self.client.db["feedback"].count_documents(
                {"guild_id": ctx.guild.id, "staff": staff.id}
            )
        else:
            await ctx.send(f"  Invalid scope. Please use 'global' or 'server'.")
            return

        if total_ratings == 0:
            await ctx.send(
                f"  **{ctx.author.display_name}**, I couldn't find any rating for this user.\n{arrow} To rate someone use </feedback give:1194418154617700382>!",
            )
            return
        sum_ratings = sum(
            int(rating["rating"].split("/")[0]) for rating in staff_ratings
        )
        average_rating = int(sum_ratings / total_ratings)

        if total_ratings > 0:
            last_rating = staff_ratings[-1]["rating"]
        else:
            last_rating = "N/A"

        rating_text = get_rating_text(average_rating)

        embed = discord.Embed(
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="Ratings",
            value=f"> **Average Rating**: {average_rating}/10\n> **Last Rating**: {last_rating}/10\n> **Overall**: {rating_text}",
        )
        value = f"> **Author:** <@{staff_ratings[-1]['author']}>\n> **Feedback:** {staff_ratings[-1]['feedback']}"
        if len(value) > 1021:
            value = value[:1021] + "..."
        embed.add_field(
            name="Last Rating",
            value=value,
        )
        embed.set_author(name=f"@{staff.display_name}", icon_url=staff.display_avatar)
        embed.set_footer(text=f"{scope.capitalize()} Ratings")
        view = ViewRatings(staff_ratings, staff, ctx, scope, ctx.author)
        await ctx.send(embed=embed, view=view)


class ViewRatings(discord.ui.View):
    def __init__(self, ratings, staff, ctx, scope, author):
        super().__init__(timeout=120)
        self.ratings = ratings
        self.staff = staff
        self.ctx = ctx
        self.scope = scope
        self.author = author

    @discord.ui.button(
        label="View Ratings",
        style=discord.ButtonStyle.grey,
        emoji="<:stafffeedback:1235000485208002610>",
    )
    async def Ratings(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your view",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        msg = await self.ctx.send(
            embed=discord.Embed(
                description="<a:astroloading:1245681595546079285>",
                color=discord.Color.dark_embed(),
            )
        )
        if self.scope == "global":
            staff_ratings = (
                await interaction.client.db["feedback"]
                .find({"staff": self.staff.id})
                .to_list(length=None)
            )
        elif self.scope == "server":
            staff_ratings = (
                await interaction.client.db["feedback"]
                .find({"guild_id": interaction.guild.id, "staff": self.staff.id})
                .to_list(length=None)
            )
        embeds = []
        for idx, rating in enumerate(staff_ratings):
            if idx % 9 == 0:
                embed = discord.Embed(
                    title="Staff Ratings", color=discord.Color.dark_theme()
                )
                embed.set_thumbnail(url=self.staff.display_avatar)
                embed.set_author(
                    name=self.staff.display_name, icon_url=self.staff.display_avatar
                )
            date = rating.get("date", 0)
            Id = rating.get("feedbackid", "N/A")
            feedback = rating.get("feedback", "Non Given")
            value = f"> **Date:** <t:{int(date)}>\n> **Feedback ID:** {Id}\n> **Feedback:** {feedback}"
            if len(value) > 1021:
                value = value[:1021] + "..."

            embed.add_field(
                name=f"{star} {rating['rating']}/10",
                value=value,
                inline=False,
            )

            if (idx + 1) % 9 == 0 or idx == len(staff_ratings) - 1:
                embeds.append(embed)

        pag = await PaginatorButtons()
        button.disabled = True
        await pag.start(self.ctx, embeds, msg=msg)
        await interaction.response.edit_message(view=self)


def get_rating_text(average_rating):
    if average_rating >= 8:
        return "Great"
    elif average_rating >= 5:
        return "Moderate"
    else:
        return "Critical"


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Feedback(client))
