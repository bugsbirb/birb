import discord
from discord.ext import commands
from discord import app_commands
import os
import io
from datetime import datetime, timedelta
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from utils.emojis import *
from utils.Module import ModuleCheck
from utils.permissions import has_admin_role
from utils.format import IsSeperateBot
from utils.HelpEmbeds import (
    BotNotConfigured,
    ModuleNotEnabled,
    Support,
)

environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")

CHART_BG = "#2b2d31"
CHART_FG = "#e0e0e0"
ACCENT_COLORS = ["#5865f2", "#57f287", "#fee75c", "#ed4245", "#eb459e", "#ff9b2e", "#45d1e6", "#b8b8b8"]


def setup_chart_style():
    plt.rcParams.update({
        "figure.facecolor": CHART_BG,
        "axes.facecolor": CHART_BG,
        "axes.edgecolor": CHART_FG,
        "axes.labelcolor": CHART_FG,
        "text.color": CHART_FG,
        "xtick.color": CHART_FG,
        "ytick.color": CHART_FG,
        "grid.color": "#3b3d44",
        "grid.alpha": 0.5,
        "font.size": 10,
    })


def fig_to_file(fig, filename="chart.png"):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return discord.File(buf, filename=filename)


def parse_timeframe(timeframe: str) -> timedelta:
    mapping = {
        "7d": timedelta(days=7),
        "14d": timedelta(days=14),
        "30d": timedelta(days=30),
        "60d": timedelta(days=60),
        "90d": timedelta(days=90),
    }
    return mapping.get(timeframe, timedelta(days=30))


TIMEFRAME_CHOICES = [
    app_commands.Choice(name="7 days", value="7d"),
    app_commands.Choice(name="14 days", value="14d"),
    app_commands.Choice(name="30 days", value="30d"),
    app_commands.Choice(name="60 days", value="60d"),
    app_commands.Choice(name="90 days", value="90d"),
]


class Analytics(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    analytics = app_commands.Group(
        name="analytics",
        description="View staff activity analytics and charts.",
    )

    @analytics.command(name="infractions", description="View infraction trends over time.")
    @app_commands.describe(timeframe="Time period to analyze")
    @app_commands.choices(timeframe=TIMEFRAME_CHOICES)
    async def infraction_analytics(self, interaction: discord.Interaction, timeframe: str = "30d"):
        if not await has_admin_role(interaction, "Infraction Permissions"):
            return
        if not await ModuleCheck(interaction.guild.id, "infractions"):
            return await interaction.response.send_message(embed=ModuleNotEnabled(), view=Support())

        await interaction.response.defer()
        delta = parse_timeframe(timeframe)
        since = datetime.now() - delta

        infractions = await self.client.db["infractions"].find({
            "guild_id": interaction.guild.id,
            "timestamp": {"$gte": since},
        }).to_list(length=None)

        if not infractions:
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name}**, no infractions found in the last {timeframe}."
            )

        setup_chart_style()
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        dates = [i.get("timestamp", since).date() for i in infractions]
        date_counts = Counter(dates)
        all_days = []
        current = since.date()
        while current <= datetime.now().date():
            all_days.append(current)
            current += timedelta(days=1)
        counts = [date_counts.get(d, 0) for d in all_days]

        ax1.fill_between(all_days, counts, alpha=0.3, color=ACCENT_COLORS[0])
        ax1.plot(all_days, counts, color=ACCENT_COLORS[0], linewidth=2)
        ax1.set_title("Infractions Per Day", fontweight="bold")
        ax1.set_ylabel("Count")
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=45)
        ax1.grid(True, axis="y")

        type_counts = Counter(i.get("action", "Unknown") for i in infractions)
        types = list(type_counts.keys())
        values = list(type_counts.values())
        colors = ACCENT_COLORS[:len(types)]
        ax2.barh(types, values, color=colors)
        ax2.set_title("By Type", fontweight="bold")
        ax2.set_xlabel("Count")
        ax2.invert_yaxis()
        ax2.grid(True, axis="x")

        fig.suptitle(f"Infraction Analytics - Last {timeframe}", fontweight="bold", fontsize=13)
        fig.tight_layout()

        file = fig_to_file(fig, "infractions.png")
        embed = discord.Embed(
            color=discord.Color.dark_embed(),
            timestamp=datetime.now(),
        )
        embed.set_author(name="Infraction Analytics", icon_url=interaction.guild.icon)
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.add_field(
            name=f"{infractions} Overview" if not IsSeperateBot() else "Overview",
            value=(
                f"> **Total Infractions:** {len(infractions)}\n"
                f"> **Period:** Last {timeframe}\n"
                f"> **Most Common:** {type_counts.most_common(1)[0][0]} ({type_counts.most_common(1)[0][1]})"
            ),
        )
        embed.set_image(url="attachment://infractions.png")
        embed.set_footer(text=f"@{interaction.user.name}", icon_url=interaction.user.display_avatar)
        await interaction.followup.send(embed=embed, file=file)

    @analytics.command(name="promotions", description="View promotion trends over time.")
    @app_commands.describe(timeframe="Time period to analyze")
    @app_commands.choices(timeframe=TIMEFRAME_CHOICES)
    async def promotion_analytics(self, interaction: discord.Interaction, timeframe: str = "30d"):
        if not await has_admin_role(interaction, "Promotion Permissions"):
            return
        if not await ModuleCheck(interaction.guild.id, "promotions"):
            return await interaction.response.send_message(embed=ModuleNotEnabled(), view=Support())

        await interaction.response.defer()
        delta = parse_timeframe(timeframe)
        since = datetime.now() - delta

        promo_list = await self.client.db["promotions"].find({
            "guild_id": interaction.guild.id,
            "timestamp": {"$gte": since},
        }).to_list(length=None)

        if not promo_list:
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name}**, no promotions found in the last {timeframe}."
            )

        setup_chart_style()
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        dates = [p.get("timestamp", since).date() for p in promo_list]
        date_counts = Counter(dates)
        all_days = []
        current = since.date()
        while current <= datetime.now().date():
            all_days.append(current)
            current += timedelta(days=1)
        counts = [date_counts.get(d, 0) for d in all_days]

        ax1.fill_between(all_days, counts, alpha=0.3, color=ACCENT_COLORS[1])
        ax1.plot(all_days, counts, color=ACCENT_COLORS[1], linewidth=2)
        ax1.set_title("Promotions Per Day", fontweight="bold")
        ax1.set_ylabel("Count")
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=45)
        ax1.grid(True, axis="y")

        staff_counts = Counter(p.get("staff") for p in promo_list)
        top_staff = staff_counts.most_common(10)
        names = []
        for uid, _ in top_staff:
            member = interaction.guild.get_member(uid)
            if member:
                names.append(member.display_name[:15])
            else:
                names.append(str(uid))
        values = [c for _, c in top_staff]
        colors = ACCENT_COLORS[:len(names)]

        ax2.barh(names, values, color=colors)
        ax2.set_title("Most Promoted Staff", fontweight="bold")
        ax2.set_xlabel("Promotions")
        ax2.invert_yaxis()
        ax2.grid(True, axis="x")

        fig.suptitle(f"Promotion Analytics - Last {timeframe}", fontweight="bold", fontsize=13)
        fig.tight_layout()

        file = fig_to_file(fig, "promotions.png")
        embed = discord.Embed(
            color=discord.Color.dark_embed(),
            timestamp=datetime.now(),
        )
        embed.set_author(name="Promotion Analytics", icon_url=interaction.guild.icon)
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.add_field(
            name=f"{promotions} Overview" if not IsSeperateBot() else "Overview",
            value=(
                f"> **Total Promotions:** {len(promo_list)}\n"
                f"> **Period:** Last {timeframe}"
            ),
        )
        embed.set_image(url="attachment://promotions.png")
        embed.set_footer(text=f"@{interaction.user.name}", icon_url=interaction.user.display_avatar)
        await interaction.followup.send(embed=embed, file=file)

    @analytics.command(name="quota", description="View message quota distribution chart.")
    async def quota_analytics(self, interaction: discord.Interaction):
        if not await has_admin_role(interaction, "Message Quota Permissions"):
            return
        if not await ModuleCheck(interaction.guild.id, "Quota"):
            return await interaction.response.send_message(embed=ModuleNotEnabled(), view=Support())

        await interaction.response.defer()

        Config = await self.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            return await interaction.followup.send(embed=BotNotConfigured(), view=Support())
        if not Config.get("Message Quota"):
            return await interaction.followup.send(embed=ModuleNotEnabled(), view=Support())

        quota_threshold = int(Config.get("Message Quota", {}).get("quota", 0))

        users = await self.client.qdb["messages"].find({
            "guild_id": interaction.guild.id,
        }).to_list(length=None)

        if not users:
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name}**, no message data found."
            )

        from utils.permissions import check_admin_and_staff
        loa_role_id = Config.get("LOA", {}).get("role")

        passed = 0
        failed = 0
        on_loa = 0
        msg_counts = []

        for u in users:
            member = interaction.guild.get_member(u.get("user_id"))
            if not member:
                continue
            if not await check_admin_and_staff(interaction.guild, member):
                continue

            count = u.get("message_count", 0)
            msg_counts.append(count)

            if loa_role_id and any(r.id == loa_role_id for r in member.roles):
                on_loa += 1
            elif count >= quota_threshold:
                passed += 1
            else:
                failed += 1

        if not msg_counts:
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name}**, no staff message data found."
            )

        setup_chart_style()
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        sizes = [passed, failed, on_loa]
        labels = [f"Passed ({passed})", f"Failed ({failed})", f"On LOA ({on_loa})"]
        pie_colors = [ACCENT_COLORS[1], ACCENT_COLORS[3], ACCENT_COLORS[4]]
        non_zero = [(s, l, c) for s, l, c in zip(sizes, labels, pie_colors) if s > 0]
        if non_zero:
            sizes, labels, pie_colors = zip(*non_zero)
            ax1.pie(sizes, labels=labels, colors=pie_colors, autopct="%1.0f%%",
                    textprops={"color": CHART_FG}, startangle=90)
        ax1.set_title("Quota Status", fontweight="bold")

        ax2.hist(msg_counts, bins=min(20, max(5, len(msg_counts) // 3)),
                 color=ACCENT_COLORS[0], edgecolor=CHART_BG, alpha=0.8)
        if quota_threshold > 0:
            ax2.axvline(x=quota_threshold, color=ACCENT_COLORS[3], linestyle="--",
                        linewidth=2, label=f"Quota: {quota_threshold}")
            ax2.legend(facecolor=CHART_BG, edgecolor=CHART_FG)
        ax2.set_title("Message Distribution", fontweight="bold")
        ax2.set_xlabel("Messages")
        ax2.set_ylabel("Staff Count")
        ax2.grid(True, axis="y")

        fig.suptitle("Quota Analytics", fontweight="bold", fontsize=13)
        fig.tight_layout()

        total = passed + failed + on_loa
        pass_rate = f"{(passed / total * 100):.0f}%" if total > 0 else "N/A"

        file = fig_to_file(fig, "quota.png")
        embed = discord.Embed(
            color=discord.Color.dark_embed(),
            timestamp=datetime.now(),
        )
        embed.set_author(name="Quota Analytics", icon_url=interaction.guild.icon)
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.add_field(
            name="<:tablerprogressbolt:1330500442551091210> Overview" if not IsSeperateBot() else "Overview",
            value=(
                f"> **Total Staff:** {total}\n"
                f"> **Passed:** {passed} ({pass_rate})\n"
                f"> **Failed:** {failed}\n"
                f"> **On LOA:** {on_loa}\n"
                f"> **Quota Threshold:** {quota_threshold} messages"
            ),
        )
        embed.set_image(url="attachment://quota.png")
        embed.set_footer(text=f"@{interaction.user.name}", icon_url=interaction.user.display_avatar)
        await interaction.followup.send(embed=embed, file=file)

    @analytics.command(name="overview", description="View a full staff analytics overview.")
    @app_commands.describe(timeframe="Time period to analyze")
    @app_commands.choices(timeframe=TIMEFRAME_CHOICES)
    async def overview_analytics(self, interaction: discord.Interaction, timeframe: str = "30d"):
        if not await has_admin_role(interaction):
            return

        await interaction.response.defer()
        delta = parse_timeframe(timeframe)
        since = datetime.now() - delta

        infraction_list = await self.client.db["infractions"].find({
            "guild_id": interaction.guild.id,
            "timestamp": {"$gte": since},
        }).to_list(length=None)

        promo_list = await self.client.db["promotions"].find({
            "guild_id": interaction.guild.id,
            "timestamp": {"$gte": since},
        }).to_list(length=None)

        loa_list = await self.client.db["LOA"].find({
            "guild_id": interaction.guild.id,
            "accepted_on": {"$gte": since},
        }).to_list(length=None)

        tickets = await self.client.db["Ticket Quota"].find({
            "GuildID": interaction.guild.id,
        }).to_list(length=None)

        total_tickets = sum(t.get("ClaimedTickets", 0) for t in tickets)

        setup_chart_style()
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        ax = axes[0][0]
        if infraction_list:
            dates = [i.get("timestamp", since).date() for i in infraction_list]
            date_counts = Counter(dates)
            all_days = []
            current = since.date()
            while current <= datetime.now().date():
                all_days.append(current)
                current += timedelta(days=1)
            counts = [date_counts.get(d, 0) for d in all_days]
            ax.fill_between(all_days, counts, alpha=0.3, color=ACCENT_COLORS[3])
            ax.plot(all_days, counts, color=ACCENT_COLORS[3], linewidth=2)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.set_title("Infractions", fontweight="bold")
        ax.grid(True, axis="y")

        ax = axes[0][1]
        if promo_list:
            dates = [p.get("timestamp", since).date() for p in promo_list]
            date_counts = Counter(dates)
            all_days = []
            current = since.date()
            while current <= datetime.now().date():
                all_days.append(current)
                current += timedelta(days=1)
            counts = [date_counts.get(d, 0) for d in all_days]
            ax.fill_between(all_days, counts, alpha=0.3, color=ACCENT_COLORS[1])
            ax.plot(all_days, counts, color=ACCENT_COLORS[1], linewidth=2)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.set_title("Promotions", fontweight="bold")
        ax.grid(True, axis="y")

        ax = axes[1][0]
        if infraction_list:
            type_counts = Counter(i.get("action", "Unknown") for i in infraction_list)
            types = list(type_counts.keys())
            values = list(type_counts.values())
            colors = ACCENT_COLORS[:len(types)]
            ax.barh(types, values, color=colors)
            ax.invert_yaxis()
        ax.set_title("Infraction Types", fontweight="bold")
        ax.grid(True, axis="x")

        ax = axes[1][1]
        ax.axis("off")
        stats_text = (
            f"Infractions: {len(infraction_list)}\n"
            f"Promotions: {len(promo_list)}\n"
            f"LOAs Filed: {len(loa_list)}\n"
            f"Tickets Claimed: {total_tickets}"
        )
        ax.text(0.5, 0.5, stats_text, transform=ax.transAxes,
                fontsize=16, verticalalignment="center", horizontalalignment="center",
                fontfamily="monospace", color=CHART_FG,
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#3b3d44", edgecolor=CHART_FG, alpha=0.5))
        ax.set_title("Summary", fontweight="bold")

        fig.suptitle(f"Staff Overview - Last {timeframe}", fontweight="bold", fontsize=14)
        fig.tight_layout()
        for row in axes:
            for a in row:
                for label in a.get_xticklabels():
                    label.set_rotation(30)

        file = fig_to_file(fig, "overview.png")
        embed = discord.Embed(
            color=discord.Color.dark_embed(),
            timestamp=datetime.now(),
        )
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.add_field(
            name=f"{Settings} Staff Analytics" if not IsSeperateBot() else "Staff Analytics",
            value=(
                f"> **Period:** Last {timeframe}\n"
                f"> **Infractions:** {len(infraction_list)}\n"
                f"> **Promotions:** {len(promo_list)}\n"
                f"> **LOAs Filed:** {len(loa_list)}\n"
                f"> **Tickets Claimed:** {total_tickets}"
            ),
        )
        embed.set_image(url="attachment://overview.png")
        embed.set_footer(text=f"@{interaction.user.name}", icon_url=interaction.user.display_avatar)
        await interaction.followup.send(embed=embed, file=file)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Analytics(client))
