import discord
from discord.ext import commands
from discord import app_commands

from datetime import datetime
from typing import Optional

import aiohttp
from utils.emojis import *
from typing import Literal
from utils.format import IsSeperateBot
from dotenv import load_dotenv

load_dotenv()


class Utility(commands.Cog):
    def __init__(self, client):
        self.client = client
        client.launch_time = datetime.now()
        self.client.help_command = None

    async def CheckDB(self):
        try:

            await self.client.db.command("ping")
            return "Connected"
        except Exception as e:
            print(f"Error interacting with the database: {e}")
            return "Not Connected"

    @commands.hybrid_group()
    async def custom(self, ctx: commands.Context):
        return

    @custom.command(description="View our custom branding offer.")
    async def branding(self, ctx: commands.Context):
        embed = discord.Embed(color=0xFFFFFF)
        embed.set_author(
            name="Custom Branding",
            icon_url="https://cdn.discordapp.com/emojis/1238599473429483612.webp?size=96",
        )
        embed.description = "> You can get your own custom instance/bot of Astro Birb for just $4.99/£4.99 per month.\n> You will also get <:Premium:1250160559203287080> **Premium** with this!\n\n-# Disclaimer: Custom Branding isn't us selling the source code of the bot."
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Subscribe",
                style=discord.ButtonStyle.link,
                url="https://www.patreon.com/checkout/AstroBirb?rid=22733636&dhc-id=82974305222135818",
                emoji="<:Tip:1238599473429483612>",
            )
        )
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command()
    async def server(self, ctx: commands.Context):
        """Check info about current server"""
        try:
            guild = await self.client.fetch_guild(ctx.guild.id)
            owner = await self.client.fetch_user(guild.owner_id)
        except discord.errors.NotFound:
            await ctx.send("Guild not found.")
            return
        members = [member async for member in ctx.guild.fetch_members(limit=None)]
        find_bots = sum(1 for member in members if member.bot)
        human_members = sum(1 for member in members if not member.bot)
        total_members = len(members)
        text = ctx.guild.text_channels
        voice = ctx.guild.voice_channels
        guild = ctx.guild

        embed = discord.Embed(
            title=f"**{ctx.guild.name}** in a nutshell",
            description=f"<:crown:1226668264260894832> **Owner:** {owner.mention}\n<:link:1226672596284866631> **Guild:** {guild.name}\n<:ID:1226671706022740058> **Guild ID:** {guild.id}\n<:Member:1226674150463111299> **Members** {guild.member_count}\n<:pin:1226671966413389864> **Created:** <t:{guild.created_at.timestamp():.0f}:D> (<t:{guild.created_at.timestamp():.0f}:R>)\n<:Discord_channel:1226674545050783817> **Channels:** {len(ctx.guild.channels)}\n<:Role:1223077527984144474> **Roles:** {len(ctx.guild.roles)}",
            color=0x2B2D31,
        )
        embed.add_field(
            name="<:tags:1234994806829355169> Channels",
            value=f"* **Categories:** {len(ctx.guild.categories)}\n* **Text:** {len(text)}\n* **Forums:** {len(ctx.guild.forums)}\n* **Voice:** {len(voice)}",
            inline=True,
        )
        embed.add_field(
            name="<:poll:1192866397043306586> Stats",
            value=f"* **Total Members:** {total_members}\n* **Members:** {human_members}\n* **Bots:** {find_bots}\n* **Boosts:** {ctx.guild.premium_subscription_count} (Level {ctx.guild.premium_tier})\n* **Total Roles:** {len(ctx.guild.roles)}",
            inline=True,
        )

        if str(ctx.guild.explicit_content_filter).capitalize() == "All_members":
            content_filter = "Everyone"
        else:
            content_filter = {str(ctx.guild.explicit_content_filter).capitalize()}

        embed.add_field(
            name="<:Promotion:1234997026677198938> Security",
            value=f"* **Verifiy Level:** {str(ctx.guild.verification_level).capitalize()}\n* **Content Filter:** `{content_filter}`",
        )
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(name=f"{owner}'s creation", icon_url=owner.display_avatar)

        await ctx.send(embed=embed)

    @app_commands.command(description="View someones avatar")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        if user is None:
            user = interaction.user
        embed = discord.Embed(
            title=f"{(user.name).capitalize()}'s Avatar",
            color=discord.Color.dark_embed(),
        )
        embed.set_image(url=user.display_avatar)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def user(
        self, interaction: discord.Interaction, user: Optional[discord.User] = None
    ) -> None:
        """Displays user's information"""
        await interaction.response.defer()

        if user is None:
            user = interaction.user

        UserBadges = self.client.db["User Badges"].find({"user_id": user.id})
        BadgeValues = ""

        Badges = {
            "staff": "<:Staff:1221449338744602655>",
            "partner": "<:blurple_partner:1221449485792841791>",
            "hypesquad": "<:hypesquad_events:1221444926995169361>",
            "bug_hunter_level_2": "<:bug_hunter_2:1221449642328457237>",
            "bug_hunter": "<:Discord_Bughunter:1285251213159436288>",
            "hypesquad_bravery": "<:hypesquad_bravery:1221444906409660529>",
            "hypesquad_brilliance": "<:hypesquad_brilliance:1221444915515490334>",
            "hypesquad_balance": "<:hypesquad_balance:1221444890827817090>",
            "early_supporter": "<:early:1221444939733536868>",
            "verified_bot": "<:Twitter_VerifiedBadge:1221450046625812591>",
            "verified_developer": "<:verified:1221450133997097052>",
            "active_developer": "<:Active_Developer_Badge:1221444993873477714>",
            "booster": "<:boost:1231403830390816808>",
            "Premium": "<:Premium:1250160559203287080>",
        }

        BadgeCount = 0
        async for BadgeData in UserBadges:
            Badge = BadgeData["badge"]
            BadgeValues += f"> {Badge}\n"
            BadgeCount += 1

        Member = None
        if interaction.guild:
            try:
                Guild = await self.client.fetch_guild(1092976553752789054)
            except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                Guild = None
            try:
                if Guild:
                    Member = await Guild.fetch_member(user.id)
                    if Member:
                        RolesToCheck = {
                            "booster": 1160541890035339264,
                            "donator": 1229172969830617199,
                            "donator2": 1182011116650496031,
                            "premium": 1233945875680596010,
                        }
                        for RoleName, RoleID in RolesToCheck.items():
                            Role = Guild.get_role(RoleID)
                            if Role in Member.roles:
                                BadgeValues += f"> {Badges.get(RoleName, '')} {RoleName.capitalize()}\n"
                                BadgeCount += 1

                    Member = await interaction.guild.fetch_member(user.id)
            except (discord.HTTPException, discord.NotFound):
                pass

        UserFlags = user.public_flags.all()
        for Flag in UserFlags:
            FlagName = Flag.name
            if FlagName in Badges:
                FlagDisplayName = FlagName.replace("_", " ").title()
                if FlagDisplayName == "Bug Hunter Level 2":
                    FlagDisplayName = "Bug Hunter"
                BadgeValues += f"> {Badges[FlagName]} {FlagDisplayName}\n"
                BadgeCount += 1

        Embed = discord.Embed(
            title=f"@{user.display_name}",
            description="",
            color=(
                user.accent_colour or Member.top_role.color
                if Member
                else discord.Color.dark_embed()
            ),
        )

        Embed.set_thumbnail(url=user.display_avatar.url)

        if UserFlags or BadgeValues:
            Embed.add_field(name=f"Flags [{BadgeCount}]", value=BadgeValues)

        Embed.add_field(
            name="**Profile**",
            value=f"> **User:** {user.mention}\n> **Display:** {user.display_name}\n> **ID:** {user.id}\n> **Join:** <t:{int(user.joined_at.timestamp())}:F>\n> **Created:** <t:{int(user.created_at.timestamp())}:F>",
            inline=False,
        )

        if Member:
            UserRoles = " ".join(
                [
                    Role.mention
                    for Role in reversed(Member.roles)
                    if Role != interaction.guild.default_role
                ][:20]
            )
            RoleCount = len(Member.roles) - 1
            Embed.add_field(
                name=f"**Roles** [{RoleCount}]", value=UserRoles, inline=False
            )

        await interaction.followup.send(embed=Embed)

    async def fetch_birb_image(self):
        birb_api_url = "https://api.alexflipnote.dev/birb"
        async with aiohttp.ClientSession() as session, session.get(
            birb_api_url
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data["file"]

    @app_commands.command(name="birb", description="Get silly birb photo")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def birb(self, interaction: discord.Interaction):
        try:
            birb_image_url = await self.fetch_birb_image()

            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_image(url=birb_image_url)
            await interaction.response.send_message(embed=embed)

        except aiohttp.ClientError as e:
            await interaction.response.send_message(
                f"  {interaction.user.mention}, I couldn't get a birb image for you :c\n**Error:** `{e}`",
            )

    @app_commands.command(name="ping", description="Check the bots latency & uptime")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer()
        server_name = "Astro Birb"
        server_icon = self.client.user.display_avatar
        discord_latency = self.client.latency * 1000
        discord_latency_message = f"**Latency:** {discord_latency:.0f}ms"
        database_status = await self.CheckDB()
        embed = discord.Embed(
            title="<:Network:1223063016677838878> Network Information",
            description=f"{discord_latency_message}\n**Database:** {database_status}\n**Uptime:** <t:{int(self.client.launch_time.timestamp())}:R>",
            color=0x2B2D31,
        )

        embed.set_author(name=server_name, icon_url=server_icon)
        embed.set_thumbnail(url=server_icon)
        view = NetWorkPage(self.client, interaction.user)
        if IsSeperateBot():
            view.left.label = "◀"
            view.Right.label = "▶"

        if interaction.guild:
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.followup.send(embed=embed)

    @app_commands.command(description="Get support from the support server")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def support(self, interaction: discord.Interaction):
        view = Support()
        bot_user = self.client.user
        embed = discord.Embed(
            description="Encountering issues with Astro Birb? Our support team is here to help! Join our official support server using the link below.",
            color=0x2B2D31,
        )
        embed.set_author(name=bot_user.display_name, icon_url=bot_user.display_avatar)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(description="Invite Astro Birb to your server")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def invite(self, interaction: discord.Interaction):
        view = invite()
        await interaction.response.send_message(view=view)

    @commands.hybrid_command(description="Buy or manage your premium!")
    async def premium(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        embed = discord.Embed(
            title="",
            color=discord.Color.blurple(),
        )
        embed.description = """
            ## 🎁 Premium Benefits

            - More Custom Commands (10 -> ∞)
            - Premium Badge
            - Unlimited Modmail Categories
            - Mass Promotion
            - Mass Infractions (You can infract more than one person at a time)
            - Auto Response Module (Levenshtein)
            - Infraction Reason Presets
            - Punish Failures (Automatic Quota Punishment)
            - Lock/Close buttons on thread autoposts.
            """

        embed.set_thumbnail(url=self.client.user.display_avatar)
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Premium",
                emoji="<:sparkle:1233931758089666695>",
                style=discord.ButtonStyle.link,
                url="https://patreon.com/astrobirb",
            )
        )
        await ctx.send(embed=embed, view=view)
        return

    @app_commands.command(name="vote", description="❤️ Support Astro Birb!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def vote(self, interaction: discord.Interaction):
        embed = discord.Embed(
            description="Hi there! If you enjoy using **Astro Birb**, consider upvoting it on the following platforms to help us grow and reach more servers. Your support means a lot!",
            color=discord.Color.dark_embed(),
        )
        button = discord.ui.Button(
            label="Upvote",
            url="https://top.gg/bot/1113245569490616400/vote",
            emoji="<:topgg:1206665848408776795>",
            style=discord.ButtonStyle.blurple,
        )
        button3 = discord.ui.Button(
            label="Upvote",
            url="https://discords.com/bots/bot/1113245569490616400/vote",
            emoji="<:Discords_noBG:1206666304107446352>",
            style=discord.ButtonStyle.blurple,
        )
        embed.set_thumbnail(url=self.client.user.display_avatar)
        embed.set_author(
            name=self.client.user.display_name, icon_url=self.client.user.display_avatar
        )
        view = discord.ui.View()
        view.add_item(button)
        view.add_item(button3)

        await interaction.response.send_message(embed=embed, view=view)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None,
    ) -> None:
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


class NetWorkPage(discord.ui.View):
    def __init__(self, client, author):
        super().__init__(timeout=360)
        self.client = client
        self.author = author

    @discord.ui.button(
        label="",
        style=discord.ButtonStyle.grey,
        emoji="<:chevronleft:1220806425140531321>",
        disabled=True,
    )
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(
        label="Network",
        style=discord.ButtonStyle.blurple,
        emoji="<:Network:1223063016677838878>",
    )
    async def network(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.edit_message(content="")

    @discord.ui.button(
        label="",
        style=discord.ButtonStyle.grey,
        emoji="<:chevronright:1220806430010118175>",
    )
    async def Right(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        server_name = "Astro Birb"
        server_icon = self.client.user.display_avatar
        embed = discord.Embed(
            title="Sharding Information", color=discord.Color.dark_embed()
        )
        if interaction.guild:
            for shard_id, shard_instance in self.client.shards.items():
                shard_info = f"> **Latency:** {shard_instance.latency * 1000:.0f} ms\n"
                guild_count = sum(
                    1 for guild in self.client.guilds if guild.shard_id == shard_id
                )
                shard_info += f"> **Guilds:** {guild_count}\n"
                urguild = ""
                if shard_id == interaction.guild.shard_id:
                    urguild = "(This Guild)"
                embed.add_field(
                    name=f"<:pingpong:1235001064294449232> Shard {shard_id} {urguild}",
                    value=shard_info,
                    inline=False,
                )
        embed.set_author(name=server_name, icon_url=server_icon)
        embed.set_thumbnail(url=server_icon)
        view = ShardsPage(self.client, self.author)
        if IsSeperateBot():
            view.left.label = "◀"
            view.Right.label = "▶"
        await interaction.response.edit_message(
            embed=embed, view=view
        )


class ShardsPage(discord.ui.View):
    def __init__(self, client, author):
        super().__init__()
        self.client = client
        self.author = author

    async def CheckDB(self):
        try:

            await self.client.db.command("ping")
            return "Connected"
        except Exception as e:
            return "Not Connected"

    @discord.ui.button(
        label="",
        style=discord.ButtonStyle.grey,
        emoji="<:chevronleft:1220806425140531321>",
        disabled=False,
    )
    async def left(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        server_name = "Astro Birb"
        server_icon = self.client.user.display_avatar
        discord_latency = self.client.latency * 1000
        discord_latency_message = f"**Latency:** {discord_latency:.0f}ms"
        database_status = await self.CheckDB()
        embed = discord.Embed(
            title="<:Network:1223063016677838878> Network Information",
            description=f"{discord_latency_message}\n**Database:** {database_status}\n**Uptime:** <t:{int(self.client.launch_time.timestamp())}:R>",
            color=0x2B2D31,
        )

        embed.set_author(name=server_name, icon_url=server_icon)
        embed.set_thumbnail(url=server_icon)
        view = NetWorkPage(self.client, interaction.user)
        if IsSeperateBot():
            view.left.label = "◀"
            view.Right.label = "▶"
        await interaction.response.edit_message(
            embed=embed, view=view
        )

    @discord.ui.button(
        label="Shards",
        style=discord.ButtonStyle.blurple,
        emoji="<:pingpong:1235001064294449232>",
    )
    async def shards(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="")

    @discord.ui.button(
        label="",
        style=discord.ButtonStyle.grey,
        emoji="<:chevronright:1220806430010118175>",
        disabled=True,
    )
    async def Right(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass


class invite(discord.ui.View):
    def __init__(self):
        super().__init__()
        url = "https://discord.com/api/oauth2/authorize?client_id=1113245569490616400&permissions=1632557853697&scope=bot%20applications.commands"
        self.add_item(
            discord.ui.Button(
                label="Invite",
                url=url,
                style=discord.ButtonStyle.blurple,
                emoji="<:link:1206670134064717904>",
            )
        )


class Support(discord.ui.View):
    def __init__(self):
        super().__init__()
        url = "https://discord.gg/DhWdgfh3hN"
        self.add_item(
            discord.ui.Button(
                label="Join",
                url=url,
                style=discord.ButtonStyle.blurple,
                emoji="<:link:1206670134064717904>",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Documentation",
                url="https://docs.astrobirb.dev",
                style=discord.ButtonStyle.blurple,
                emoji="📚",
            )
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Utility(client))
