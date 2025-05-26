import discord
from discord.ext import commands, tasks
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
import aiohttp
import os
from discord import app_commands
from datetime import datetime
from utils.emojis import *

matplotlib.use("Agg")
import numpy as np
from scipy.interpolate import CubicSpline


class Ping(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.SavePing.start()

    async def Gen(self, data: dict) -> BytesIO:
        blurple = "#5865F2"
        green = "#57F287"
        background = "#2b2d31"
        GridColor = "#4f545c"
        TextColor = "#b9bbbe"
        purple = "#9b59b6"

        plt.rcParams.update(
            {
                "axes.edgecolor": TextColor,
                "axes.labelcolor": TextColor,
                "xtick.color": TextColor,
                "ytick.color": TextColor,
                "font.family": "DejaVu Sans",
                "axes.facecolor": background,
                "figure.facecolor": background,
                "grid.color": GridColor,
                "text.color": TextColor,
            }
        )

        plt.figure(figsize=(10, 5))

        keys = ["Latency", "DB", "API"]
        colors = {"Latency": blurple, "DB": green, "API": purple}

        for key in keys:
            if key in data and data[key]:
                y = [float(x) if x not in ["N/A", "None"] else 0 for x in data[key]]
                x = np.arange(len(y))

                cs = CubicSpline(x, y)
                x_new = np.linspace(x.min(), x.max(), 500)
                y_new = cs(x_new)

                plt.plot(
                    x_new,
                    y_new,
                    label=key,
                    color=colors[key],
                    linewidth=3,
                    linestyle="-",
                    alpha=1.0,
                )

        plt.xticks([])
        plt.legend(facecolor=background, edgecolor="none", fontsize=18, fancybox=True)
        plt.grid(True, linestyle="--", linewidth=0.5)
        plt.ylim(0, 400)
        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=100)
        buffer.seek(0)
        plt.close()
        return buffer

    async def DbConnection(self) -> str:
        try:
            await self.client.db.command("ping")
            return "Connected"
        except Exception:
            return "Not Connected"

    async def APIConnection(self) -> str:
        try:
            async with aiohttp.ClientSession() as session, session.get(
                "https://api.astrobirb.dev/status"
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError:
            return {"status": "Not Connected", "uptime": 0}

    @tasks.loop(minutes=5)
    async def SavePing(self):
        if os.getenv("ENVIRONMENT") in ["development", "custom"]:
            return
        Latency = (
            round(self.client.latency * 1000)
            if not np.isnan(self.client.latency)
            else 0
        )
        if Latency > 700:
            return

        DbLatency = None
        try:
            Start = datetime.now()
            await self.client.db.command("ping")
            DbLatency = (datetime.now() - Start).total_seconds() * 1000
            if DbLatency > 700:
                return
        except Exception:
            DbLatency = None

        API = None
        try:
            Start = datetime.now()
            await self.APIConnection()
            API = (datetime.now() - Start).total_seconds() * 1000
            if API > 700:
                return
        except Exception:
            API = None

        await self.client.db["Ping"].update_one(
            {"_id": 0},
            {
                "$push": {
                    "Latency": {"$each": [str(Latency)], "$slice": -30},
                    "DB": {
                        "$each": [str(DbLatency) if DbLatency is not None else "100"],
                        "$slice": -30,
                    },
                    "API": {"$each": [str(API) if API is not None else "100"], "$slice": -30},
                },
                "$setOnInsert": {"_id": 0},
            },
            upsert=True,
        )

    @app_commands.command(name="ping", description="Check the bot's latency")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ping(self, interaction: discord.Interaction):
        data = await self.client.db["Ping"].find_one({"_id": 0})
        API = await self.APIConnection()
        await interaction.response.defer()
        graph = await self.Gen(data)
        file = discord.File(graph, filename="ping_graph.png")

        Dis = (
            round(self.client.latency * 1000)
            if not np.isnan(self.client.latency)
            else 0
        )
        try:
            Start = datetime.now()
            await self.client.db.command("ping")
            DbLatency = (datetime.now() - Start).total_seconds() * 1000
        except Exception:
            DbLatency = None
        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(
            name=self.client.user.name, icon_url=self.client.user.display_avatar
        )
        try:
            Start = datetime.now()
            A = await self.APIConnection()
            API = (datetime.now() - Start).total_seconds() * 1000
        except Exception:
            API = None
        Z = ""
        if interaction.guild:
            Z = f"\n> **Shard ({interaction.guild.shard_id}):** `{self.client.shards[interaction.guild.shard_id].latency * 1000:.0f} ms`"

        embed.add_field(
            name="Bot",
            value=f"> **Latency:** `{Dis} ms` {Z}\n> **Uptime:** <t:{int(self.client.launch_time.timestamp())}:R>",
            inline=False,
        )
        embed.add_field(
            name="Database",
            value=f"> **Latency:** `{round(DbLatency if DbLatency else 'N/A')} ms`\n> **Status:** `{await self.DbConnection()}`",
            inline=False,
        )

        embed.add_field(
            name="API",
            value=f"> **Latency:** `{round(API) if isinstance(API, (int, float)) else 'N/A'} ms`\n> **Status:** `{A.get('status', 'N/A') if isinstance(A, dict) else 'N/A'}`\n> **Uptime:** <t:{int(A.get('uptime', 0)) if isinstance(A, dict) else 0}:R>",
            inline=False,
        )

        embed.set_image(url="attachment://ping_graph.png")

        await interaction.followup.send(embed=embed, file=file)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Ping(client))
