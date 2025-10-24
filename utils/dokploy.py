import discord
from discord.ext import commands, tasks
import os
from utils.emojis import *
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
import re
from utils.patreon import SubscriptionUser
from utils.format import IsSeperateBot
from datetime import datetime
from utils.HelpEmbeds import NotYourPanel


MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["astro"]
premium = db["Subscriptions"]
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
        "environmentId": "env_prod_AnhFqj439TjExphKiI7-x_1757255169.949818"
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
    url = f"{os.getenv('DOCKER_URL')}/api/application.update"
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


async def DeleteApplication(AppID: int):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{os.getenv('DOCKER_URL')}/api/application.delete",
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
                f"{no} **{interaction.user.display_name}**, I couldn't find that application.",
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
                content=f"{no} **{interaction.user.display_name}**, I couldn't deploy that application.",
            )
        await msg.edit(
            content=f"{tick} **{interaction.user.display_name}**, I've deployed that application.",
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
                content=f"{no} **{interaction.user.display_name}**, I couldn't start that application.",
            )
        await msg.edit(
            content=f"{tick} **{interaction.user.display_name}**, I've started that application.",
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
                content=f"{no} **{interaction.user.display_name}**, I couldn't reload that application.",
            )
        await msg.edit(
            content=f"{tick} **{interaction.user.display_name}**, I've reloaded that application.",
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
                content=f"{no} **{interaction.user.display_name}**, I couldn't deploy all applications.",
            )
        await msg.edit(
            content=f"{tick} **{interaction.user.display_name}**, I've deployed all applications.",
        )


class Depl(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.SubscriptionStatus.start()
        self.SubscriptionRoles.start()

    @tasks.loop(hours=12)
    async def SubscriptionRoles(self):
        await self.client.wait_until_ready()
        if IsSeperateBot():
            return
        if os.getenv("ENVIRONMENT") in ["custom", "development"]:
            return
        Guild = self.client.get_guild(1092976553752789054)
        PremiumRole = Guild.get_role(1233945875680596010)
        BrandingRole = Guild.get_role(1182022232407543981)
        if not PremiumRole or not BrandingRole:
            return
        PremiumMembers = set()
        BrandingMembers = set()
        for member in Guild.members:
            if PremiumRole in member.roles:
                PremiumMembers.add(member.id)
            if BrandingRole in member.roles:
                BrandingMembers.add(member.id)

        for B in BrandingMembers:
            U = await SubscriptionUser(UserID=B, Sub="22733636")
            if U:
                _, has_branding, _ = U
                if not has_branding:
                    member = Guild.get_member(B)
                    if member and BrandingRole in member.roles:
                        try:
                            await member.remove_roles(
                                BrandingRole, reason="Custom branding expired"
                            )
                        except (discord.Forbidden, discord.HTTPException):
                            pass
        for P in PremiumMembers:
            U = await SubscriptionUser(UserID=P, Tiers=["22733636", "22855340"])
            if U:
                _, _, HAs = U
                if not HAs:
                    member = Guild.get_member(P)
                    if member and PremiumRole in member.roles:
                        try:
                            await member.remove_roles(
                                PremiumRole, reason="Premium expired"
                            )
                        except (discord.Forbidden, discord.HTTPException):
                            pass

    @tasks.loop(hours=6)
    async def SubscriptionStatus(self):
        await self.client.wait_until_ready()
        if IsSeperateBot():
            return
        if os.getenv("ENVIRONMENT") in ["custom", "development"]:
            return
        Bots = await self.client.db["bots"].find({}).to_list(length=None)
        Sub = await self.client.db["Subscriptions"].find({}).to_list(length=None)
        guild = self.client.get_guild(1092976553752789054)
        for P in Sub:
            Z = await SubscriptionUser(
                UserID=P.get("user"), Tiers=["22733636", "22855340"]
            )
            if Z is None:
                continue            
            _, _, HasPremium = Z
            if not HasPremium:
                print(f"Premium expired for user {P.get('user')}")
                for guild_id in P.get("guilds", []):
                    config = await self.client.db["Config"].find_one({"_id": guild_id})
                    if config is not None:
                        features = config.get("Features", [])
                        if "PREMIUM" in features:
                            features.remove("PREMIUM")
                            await self.client.db["Config"].update_one(
                                {"_id": guild_id},
                                {"$set": {"Features": features}},
                            )
                await premium.delete_one({"user": P.get("user")})

                if guild:
                    member = guild.get_member(P.get("user"))
                    if member:
                        role = guild.get_role(1233945875680596010)
                        if role and role in member.roles:
                            try:
                                await member.remove_roles(
                                    role, reason="Premium expired"
                                )
                            except Exception as e:
                                pass

                try:
                    Owner = await self.client.fetch_user(1092976553752789054)
                    await Owner.send(
                        f"Premium expired for user <@{P.get('user')}>. Their premium status has been removed and all associated servers have lost premium features."
                    )
                except:
                    pass

        for B in Bots:
            Z = await SubscriptionUser(UserID=B.get("user"), Sub="22733636")
            if Z is None:
                continue
            _, HasBranding, _ = Z
            if not HasBranding:
                if guild:
                    member = guild.get_member(B.get("user"))
                    if member:
                        role = guild.get_role(1182022232407543981)
                        Premium = guild.get_role(1233945875680596010)
                        if role and role in member.roles:
                            try:
                                await member.remove_roles(
                                    role, reason="Custom branding expired"
                                )
                            except (discord.Forbidden, discord.HTTPException):
                                pass

                        if Premium and Premium in member.roles:
                            try:
                                await member.remove_roles(
                                    Premium, reason="Premium expired"
                                )
                            except (discord.Forbidden, discord.HTTPException):
                                pass
                            try:
                                await member.remove_roles(
                                    role, reason="Custom branding expired"
                                )
                            except (discord.Forbidden, discord.HTTPException):
                                pass

                try:
                    if not B.get("user") or not isinstance(B.get("user"), int):
                        continue
                    User = await self.client.fetch_user(int(B.get("user")))
                except:
                    continue
                name = re.sub(r"[^a-zA-Z0-9]", "", User.name)
                Projects = await GetProjects()
                if Projects:
                    for project in Projects.get("applications", []):
                        if project.get("name") == name:
                            print(
                                f"Branding expired for user {B.get('user')} - stopping application {project.get('applicationId')}"
                            )
                            await StopApplication(project.get("applicationId"))
                            try:
                                Owner = await self.client.fetch_user(
                                    1092976553752789054
                                )
                                await Owner.send(
                                    f"Branding expired for user <@{B.get('user')}> - application {project.get('applicationId')} has been stopped."
                                )
                            except:
                                pass
                            break

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if not before.guild.id == 1092976553752789054:
            return

        if not before.guild.chunked:
            await before.guild.chunk()
        if isinstance(before, discord.Member) and isinstance(after, discord.Member):
            if after.guild is None:
                return

            role = discord.utils.get(after.guild.roles, id=1182022232407543981)
            prem = discord.utils.get(after.guild.roles, id=1233945875680596010)
            botrole = discord.utils.get(after.guild.roles, id=1279097432482775051)
            if role:
                if role in before.roles and role not in after.roles:
                    embed = discord.Embed(
                        title="🚫 Custom Branding Expired",
                        description=(
                            f"Hey {after.mention},\n\n"
                            f"Your **custom branding** subscription has expired and your bot has been powered off.\n\n"
                            "To continue using custom branding, please renew your subscription via [Patreon](https://patreon.com/astrobirb)."
                        ),
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow(),
                    )
                    embed.set_thumbnail(
                        url=(
                            after.display_avatar.url
                            if hasattr(after.display_avatar, "url")
                            else after.display_avatar
                        )
                    )
                    embed.set_footer(text="Birb • astrobirb.dev")
                    await after.send(embed=embed)

                    Owner = discord.Embed(
                        title="Custom Branding Expired",
                        description=f"**{after.name}**'s custom branding has expired and the bot has been stopped.",
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow(),
                    )
                    Owner.set_thumbnail(
                        url=(
                            after.display_avatar.url
                            if hasattr(after.display_avatar, "url")
                            else after.display_avatar
                        )
                    )
                    Owner.set_footer(text=f"User ID: {after.id}")
                    await after.guild.owner.send(embed=Owner)

                    name = re.sub(r"[^a-zA-Z0-9]", "", after.name)
                    Projects = await GetProjects()
                    for project in Projects.get("applications", []):
                        if project.get("name") == name:
                            await StopApplication(project.get("applicationId"))
                            await after.guild.owner.send(
                                f"{tick} **@{after.name}** branding has been stopped successfully."
                            )
                            break

                if role not in before.roles and role in after.roles:
                    embed = discord.Embed(
                        title="✨ Welcome to Custom Branding!",
                        description=(
                            f"Hey {after.mention},\n\n"
                            "You're now eligible for **Custom Branding**!\n"
                            "To get started, please open a ticket in "
                            "https://discord.com/channels/1092976553752789054/1250156302831718461\n\n"
                            "Our team will guide you through the setup process."
                        ),
                        color=discord.Color.gold(),
                        timestamp=datetime.utcnow(),
                    )
                    embed.set_thumbnail(
                        url=(
                            after.display_avatar.url
                            if hasattr(after.display_avatar, "url")
                            else after.display_avatar
                        )
                    )
                    embed.set_footer(text="Birb • astrobirb.dev")
                    await after.send(embed=embed)
            if botrole:
                if botrole in before.roles and botrole in after.roles:
                    print("[KICKING] Bot Account")
                    await after.kick(reason="Bot account")
                    return

            if prem:
                if prem in before.roles and prem not in after.roles:
                    embed = discord.Embed(
                        title="💔 Premium Expired",
                        description=(
                            f"Hey {after.mention},\n\n"
                            "Your **Premium** subscription has expired.\n\n"
                            "To regain access to premium features, please renew your subscription via [Patreon](https://patreon.com/astrobirb)."
                        ),
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow(),
                    )
                    embed.set_thumbnail(
                        url=(
                            after.display_avatar.url
                            if hasattr(after.display_avatar, "url")
                            else after.display_avatar
                        )
                    )
                    embed.set_footer(text="Birb • astrobirb.dev")
                    await after.send(embed=embed)

                    Owner = discord.Embed(
                        title="Premium Expired",
                        description=f"**{after.name}**'s premium has expired.",
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow(),
                    )
                    Owner.set_thumbnail(
                        url=(
                            after.display_avatar.url
                            if hasattr(after.display_avatar, "url")
                            else after.display_avatar
                        )
                    )
                    Owner.set_footer(text=f"User ID: {after.id}")
                    await after.guild.owner.send(embed=Owner)
                    PR = await premium.find_one({"user": after.id})
                    if PR:
                        for server in PR.get("guilds", []):
                            Config = await self.client.db["Config"].find_one(
                                {"_id": server}
                            )
                            if Config is not None:
                                features = Config.get("Features", [])
                                if "PREMIUM" in features:
                                    features.remove("PREMIUM")
                                    await self.client.db["Config"].update_one(
                                        {"_id": server},
                                        {"$set": {"Features": features}},
                                    )
                        await premium.delete_one({"user": after.id})

                if prem not in before.roles and prem in after.roles:
                    embed = discord.Embed(
                        title="🎉 Welcome to Premium!",
                        description=(
                            f"Hey {after.mention},\n\n"
                            "You're now a **Premium** member!\n\n"
                            "• Go to `/config` → **Subscriptions** and activate your server.\n"
                            "• If your subscription isn't active, run `/premium`.\n\n"
                            "Need help? Visit our [Support Channel]"
                            "(https://discord.com/channels/1092976553752789054/1328460590120702094)."
                        ),
                        color=discord.Color.gold(),
                        timestamp=datetime.utcnow(),
                    )
                    embed.set_thumbnail(
                        url=(
                            after.display_avatar.url
                            if hasattr(after.display_avatar, "url")
                            else after.display_avatar
                        )
                    )
                    embed.set_footer(text="Birb • astrobirb.dev")
                    await after.send(embed=embed)
                    await premium.update_one(
                        {"user": after.id},
                        {"$set": {"user": after.id, "Tokens": 1, "guilds": []}},
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
                f"{no} **{ctx.author.display_name}**, I couldn't find any projects."
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
             
            return await interaction.response.send_message(embed=NotYourPanel(), ephemeral=True)

        result = await bots.find_one({"user_id": self.author.id})
        if result:
            return await interaction.response.send_message(
                content=f"{no} You already have a bot setup.", ephemeral=True
            )

        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(name="Custom Bot Setup", icon_url=interaction.guild.icon)
        embed.description = (
            "**Welcome to the bot setup!**\n\n"
            "This guide will help you create and launch your own Discord bot.\n\n"
            "📌 **Follow this step-by-step guide**\n"
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
             
            return await interaction.response.send_message(embed=NotYourPanel(), ephemeral=True)
        result = await bots.find_one({"user_id": interaction.user.id})
        if result:
            return await interaction.response.send_message(
                content=f"{no} You already have a bot setup.", ephemeral=True
            )

        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(name="Setting Up Your Bot", icon_url=interaction.guild.icon)
        embed.description = (
            "Now it's time to **power up your bot!**\n\n"
            "You'll need to gather the following information\n"
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
             
            return await interaction.response.send_message(embed=NotYourPanel(), ephemeral=True)
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
                f"PatreonClientID={os.getenv('PatreonClientID')}"
                f"PatreonClientSecret={os.getenv('PatreonClientSecret')}"
            )
            env = await UpdateENV(ProjectID, environment)
            if not env:
                return await interaction.response.send_message(
                    content=f"{crisis} **{interaction.user.display_name},** <@795743076520820776> the env update didn't work."
                )
        else:
            return await interaction.response.send_message(
                content=f"{crisis} **{interaction.user.display_name},** <@795743076520820776> this isn't working."
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
