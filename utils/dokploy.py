# cog
import discord
from discord.ext import commands
import os
from utils.emojis import *
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
from dotenv import load_dotenv
import re
from datetime import datetime

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["astro"]
premium = db["premium"]
bots = db["bots"]


async def DeployAll():
    projects = await GetProjects()
    if not projects:
        return False
    for project in projects.get("applications"):
        await Deploy(project.get("applicationId"))
    return True


async def Create(name, user: discord.User):
    url = f"{os.getenv('DOCKER_URL')}/api/application.create"
    headers = {
        "x-api-key": f"{os.getenv('DOCKER_TOKEN')}",
        "Content-Type": "application/json",
    }

    project_id = "AnhFqj439TjExphKiI7-x"

    data = {
        "name": str(name),
        "appName": f"custom-{name}",
        "description": f"{user.id} - {datetime.now().isoformat()}",
        "projectId": project_id,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                Response = await response.json()
                print(Response)
                return Response["applicationId"]
            else:
                print(await response.text())
                return None


async def UpdateENV(application_id, env, build_args=None):
    url = "https://birb.lgm.lol/api/application.update"
    headers = {
        "x-api-key": f"{os.getenv('DOCKER_TOKEN')}",
        "Content-Type": "application/json",
    }

    data = {
        "applicationId": application_id,
        "env": env,
        "buildArgs": build_args if build_args else "",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if not response.ok:
                return None
            return response.status


async def GetProjects():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{os.getenv('DOCKER_URL')}/api/project.one?projectId=AnhFqj439TjExphKiI7-x",
            headers={"x-api-key": f"{os.getenv('DOCKER_TOKEN')}"},
        ) as r:
            if r.status == 200:
                data = await r.json()
                return data
            else:
                print(await r.text())

                return None


async def StopApplication(AppID: int):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{os.getenv('DOCKER_URL')}/api/application.stop",
            json={"applicationId": AppID},
            headers={
                "x-api-key": f"{os.getenv('DOCKER_TOKEN')}",
                "Content-Type": "application/json",
            },
        ) as r:
            if r.status == 200:
                return True
            else:
                return None


async def GetApplication(AppID: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{os.getenv('DOCKER_URL')}/api/application.one?applicationId={AppID}",
            headers={"x-api-key": f"{os.getenv('DOCKER_TOKEN')}"},
        ) as r:
            if r.status == 200:
                data = await r.json()
                return data
            else:
                return None


async def Deploy(applicationId):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{os.getenv('DOCKER_URL')}/api/application.deploy",
            json={"applicationId": applicationId},
            headers={
                "x-api-key": f"{os.getenv('DOCKER_TOKEN')}",
                "Content-Type": "application/json",
            },
        ) as r:
            if r.status == 200:
                return True
            else:
                return None


async def Reload(applicationId):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{os.getenv('DOCKER_URL')}/api/application.reload",
            json={"applicationId": applicationId},
            headers={
                "x-api-key": f"{os.getenv('DOCKER_TOKEN')}",
                "Content-Type": "application/json",
            },
        ) as r:
            if r.status == 200:
                return True
            else:
                return None


async def Start(applicationId):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{os.getenv('DOCKER_URL')}/api/application.start",
            json={"applicationId": applicationId},
            headers={
                "x-api-key": f"{os.getenv('DOCKER_TOKEN')}",
                "Content-Type": "application/json",
            },
        ) as r:
            if r.status == 200:
                data = await r.json()
                return True
            else:
                return None


class SelectProject(discord.ui.Select):
    def __init__(self, options: list, author: discord.Member):
        super().__init__(
            placeholder="Select a project to manage",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.author = author
        self.options = options

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your view",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer()
        application = await GetApplication(self.values[0])
        if not application:
            return await interaction.followup.send(
                f"  **{interaction.user.display_name}**, I couldn't find that application.",
                ephemeral=True,
            )
        embed = discord.Embed(
            description=f"> {application.get('description')}",
            color=discord.Color.dark_embed(),
        )
        embed.set_author(
            name=f"{application.get('name')}",
            icon_url="https://cdn.discordapp.com/emojis/1327948440755372063.webp?size=96",
        )
        embed.add_field(
            name="Logs", value=f"> **@{interaction.user.name}** opened the application"
        )
        view = ManageApplication(application, interaction.user)
        view.add_item((SelectProject(self.options, interaction.user)))
        await interaction.edit_original_response(view=view, embed=embed)


class ManageApplication(discord.ui.View):
    def __init__(self, application, author: discord.Member):
        super().__init__()
        self.application = application
        self.author = author

    async def Logs(self, interaction: discord.Interaction, type: str):
        embed = interaction.message.embeds[0]
        value = embed.fields[0].value
        value += f"\n> **@{interaction.user.name}** {type} the application"
        embed.set_field_at(0, name="Logs", value=value)
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label="Deploy", style=discord.ButtonStyle.green)
    async def deploys(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your view",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer()
        msg = await interaction.followup.send(
            "<a:Loading:1167074303905386587> Deploying...", ephemeral=True
        )
        result = await Deploy(self.application.get("applicationId"))
        if not result:
            return await msg.edit(
                content=f"  **{interaction.user.display_name}**, I couldn't deploy that application.",
            )
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, I've deployed that application.",
        )
        await self.Logs(interaction, "deployed")

    @discord.ui.button(label="Start", style=discord.ButtonStyle.grey)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your view",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer()
        msg = await interaction.followup.send(
            "<a:Loading:1167074303905386587> Starting...", ephemeral=True
        )
        result = await Start(self.application.get("applicationId"))
        if not result:
            return await msg.edit(
                content=f"  **{interaction.user.display_name}**, I couldn't start that application.",
            )
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, I've started that application.",
        )
        await self.Logs(interaction, "started")

    @discord.ui.button(label="Reload", style=discord.ButtonStyle.blurple)
    async def reload(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your view",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer()
        msg = await interaction.followup.send(
            "<a:Loading:1167074303905386587> Reloading...", ephemeral=True
        )

        result = await Reload(self.application.get("applicationId"))
        if not result:
            return await msg.edit(
                content=f"  **{interaction.user.display_name}**, I couldn't reload that application.",
            )
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, I've reloaded that application.",
        )
        await self.Logs(interaction, "reloaded")


class DeployAllButton(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    @discord.ui.button(label="Deploy All", style=discord.ButtonStyle.red)
    async def deploy_all(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your view",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer()
        msg = await interaction.followup.send(
            "<a:Loading:1167074303905386587> Deploying all applications...",
            ephemeral=True,
        )
        result = await DeployAll()
        if not result:
            return await msg.edit(
                content=f"  **{interaction.user.display_name}**, I couldn't deploy all applications.",
            )
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, I've deployed all applications.",
        )


class Depl(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if isinstance(before, discord.Member) and isinstance(after, discord.Member):
            role_name = "Custom Branding"

            role = discord.utils.get(after.guild.roles, name=role_name)
            role2 = discord.utils.get(after.guild.roles, name="Premium")
            botrole = discord.utils.get(after.guild.roles, id=1279097432482775051)

            if role:
                if role in before.roles and role not in after.roles:
                    embed = discord.Embed(
                        title="Custom Branding Expired",
                        description=f"**{after.name}'s** custom branding has just expired!!!",
                        color=discord.Color.brand_red(),
                    )
                    embed.set_thumbnail(url=after.display_avatar)
                    await after.guild.owner.send(embed=embed)
                    name = re.sub(r"[^a-zA-Z0-9]", "", after.name)
                    Projects = await GetProjects()
                    for project in Projects.get("applications", []):
                        if project.get("appName") == name:
                            await StopApplication(project.get("applicationId"))
                            await after.guild.owner.send(
                                f"  **@{after.name}** branding has been stopped succesfully."
                            )
                            break

                    embed = discord.Embed(
                        title="Custom Branding Expired",
                        description="Your custom branding has RAN out. Your bot has powered off. If you want to continue, please head to [Patreon](https://patreon.com/astrobirb).",
                        color=discord.Color.brand_red(),
                    )
                    embed.set_thumbnail(url=after.display_avatar)
                    await after.send(embed=embed)

                if role not in before.roles and role in after.roles:
                    embed = discord.Embed(
                        title="🎉 Welcome to Custom Branding",
                        description="> Head over to https://discord.com/channels/1092976553752789054/1250156302831718461 and open a custom branding ticket and you will be given instructions on how to boot up your bot.",
                        color=discord.Color.yellow(),
                    )
                    embed.set_thumbnail(url=after.display_avatar)
                    await after.send(embed=embed)
            if botrole:
                if botrole in before.roles and botrole in after.roles:
                    print("[KICKING] Bot Account")
                    await after.kick(reason="Bot account")
                    return

            if role2:
                if role2 in before.roles and role2 not in after.roles:
                    embed = discord.Embed(
                        title="Premium Expired",
                        description=f"**{after.name}'s** premium has just expired!!!",
                        color=discord.Color.brand_red(),
                    )
                    embed.set_thumbnail(url=after.display_avatar)
                    await after.guild.owner.send(embed=embed)
                    await premium.delete_one({"user_id": after.id})
                    embed = discord.Embed(
                        title="Premium Expired",
                        description="Your premium has run out. If you want to continue, please head to [Patreon](https://patreon.com/astrobirb).",
                        color=discord.Color.brand_red(),
                    )
                    embed.set_thumbnail(url=after.display_avatar)
                    await after.send(embed=embed)

                if role2 not in before.roles and role2 in after.roles:
                    embed = discord.Embed(
                        title="🎉 Welcome to Premium",
                        description="> Head to /config `->` Subscriptions and then active the server!\nIf you have any questions head over to https://discord.com/channels/1092976553752789054/1328460590120702094!",
                        color=discord.Color.yellow(),
                    )
                    embed.set_thumbnail(url=after.display_avatar)
                    await after.send(embed=embed)
                    await premium.update_one(
                        {"user_id": after.id},
                        {"$set": {"user_id": after.id}},
                        upsert=True,
                    )

    @commands.command()
    @commands.is_owner()
    async def branding(self, ctx: commands.Context, user: discord.User):
        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(name="Custom Branding Setup", icon_url=ctx.guild.icon)
        embed.description = "Press **Begin Setup** to start configuring your bot."
        embed.set_footer(text=f"Setup for @{user.display_name}")

        await ctx.channel.send(embed=embed, content=user.mention, view=Setup(user))
        await ctx.message.delete()

    @commands.command()
    @commands.is_owner()
    async def docker(self, ctx: commands.Context):
        await ctx.defer()
        projects = await GetProjects()
        if not projects:
            return await ctx.send(
                f"  **{ctx.author.display_name}**, I couldn't find any projects."
            )
        embed = discord.Embed(color=discord.Color.dark_embed())
        options = []
        for project in projects.get("applications"):
            embed.add_field(
                name=f"<:Server:1327948440755372063> {project.get('name')}",
                value=f"> {project.get('description')}",
            )
            options.append(
                discord.SelectOption(
                    label=project.get("appName"),
                    value=project.get("applicationId"),
                    description=project.get("description")[:50],
                )
            )
        embed.set_author(
            name="Custom Branding", icon_url=self.client.user.display_avatar
        )
        embed.set_footer(text="Manage Applications Below")
        view = DeployAllButton(ctx.author)
        view.add_item(SelectProject(options, ctx.author))
        await ctx.send(embed=embed, view=view)


class Setup(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(label="Begin Setup", style=discord.ButtonStyle.green)
    async def begin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        result = await bots.find_one({"user_id": self.author.id})
        if result:
            return await interaction.response.send_message(
                content=f"  You already have a bot setup.", ephemeral=True
            )

        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(name="Custom Bot Setup", icon_url=interaction.guild.icon)
        embed.description = (
            "**Welcome to the bot setup!**\n\n"
            "This guide will help you create and launch your own Discord bot.\n\n"
            "📌 **Follow this step-by-step guide:**\n"
            "[Discord.py Documentation](https://discordpy.readthedocs.io/en/stable/discord.html)\n\n"
            "Click **Next** to continue."
        )
        embed.set_footer(text=f"Setup started by @{interaction.user.display_name}")

        await interaction.response.edit_message(
            embed=embed, view=Next(interaction.user)
        )


class Next(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(label="Next Step", style=discord.ButtonStyle.green)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        result = await bots.find_one({"user_id": interaction.user.id})
        if result:
            return await interaction.response.send_message(
                content=f"  You already have a bot setup.", ephemeral=True
            )

        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(name="Setting Up Your Bot", icon_url=interaction.guild.icon)
        embed.description = (
            "Now it's time to **power up your bot!**\n\n"
            "You'll need to gather the following information:\n"
            "🔹 **Bot Token** (Found in the [Discord Developer Portal](https://discord.com/developers/applications))\n"
            "🔹 **Bot Invite Link** (Used to add your bot to a server)\n"
            "🔹 **Server ID** (Where the bot will be used)\n\n"
            "Click **Continue** to enter your details."
        )
        embed.set_footer(text=f"Setup started by @{interaction.user.display_name}")
        view = Continue(interaction.user)

        await interaction.response.edit_message(embed=embed, view=view)


class Continue(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.green)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        await interaction.response.send_modal(SetUP(interaction.user.display_name))


class SetUP(discord.ui.Modal):
    def __init__(self, author: discord.Member):
        super().__init__(title="Enter Your Bot Details")
        self.author = author

        self.token = discord.ui.TextInput(
            label="Bot Token",
            style=discord.TextStyle.short,
            placeholder="Paste your bot token here (DO NOT share it with anyone).",
            required=True,
        )
        self.server = discord.ui.TextInput(
            label="Server ID",
            style=discord.TextStyle.short,
            placeholder="Enter the ID of the server where your bot will run.",
            required=True,
        )
        self.url = discord.ui.TextInput(
            label="Bot Invite Link",
            style=discord.TextStyle.short,
            placeholder="Paste your bot's invite link here.",
            required=True,
        )

        self.add_item(self.token)
        self.add_item(self.server)
        self.add_item(self.url)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(name="Finalizing Setup", icon_url=interaction.guild.icon)
        embed.description = (
            "**Your bot setup is almost complete!**\n\n"
            "✅ Your bot **should** now be online.\n"
            "⚠️ Please wait for **Bugsy** to invite your bot to the emoji servers.\n\n"
            "Here are your bot details:"
        )
        name = re.sub(r"[^a-zA-Z0-9]", "", interaction.user.name)
        ProjectID = await Create(name, interaction.user)
        if ProjectID:
            environment = (
                f"TOKEN={self.token.value}\n"
                f"MONGO_URL={MONGO_URL}\n"
                f"PREFIX=!!\n"
                f"ENVIRONMENT=custom\n"
                f"CUSTOM_GUILD={self.server.value}\n"
                f"ACCESS_KEY_ID={os.getenv('ACCESS_KEY_ID')}\n"
                f"SECRET_ACCESS_KEY={os.getenv('SECRET_ACCESS')}\n"
                f"BUCKET={os.getenv('BUCKET')}\n"
                f"FILE_URL={os.getenv('FILE_URL')}\n"
                f"R2_URL={os.getenv('R2_URL')}\n"
                f"R2_TOKEN={os.getenv('R2_TOKEN')}"
            )
            env = await UpdateENV(ProjectID, environment)
            if not env:
                return await interaction.response.send_message(
                    content=f"  **{interaction.user.display_name},** <@795743076520820776> the env update didn't work."
                )
        else:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** <@795743076520820776> this isn't working."
            )
        embed.set_footer(text=f"Setup completed by @{interaction.user.display_name}")
        embed.add_field(
            name="🔹 Server ID", value=f"```\n{self.server.value}\n```", inline=False
        )
        embed.add_field(
            name="🔹 Invite Link", value=f"```\n{self.url.value}\n```", inline=False
        )
        await bots.insert_one(
            {
                "user": interaction.user.id,
                "invite": self.url.value,
                "server": self.server.value,
                "created": datetime.now(),
            }
        )
        await interaction.response.edit_message(embed=embed, view=None)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Depl(client))
