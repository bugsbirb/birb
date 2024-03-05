import discord
from discord.ext import commands
import random
import string
from discord.ext import commands
import datetime
import Paginator
from pymongo import MongoClient
import os
from emojis import *
from datetime import datetime

from datetime import timedelta
from permissions import has_admin_role

MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client["astro"]
db = client["astro"]
collection = db["infractions"]
scollection = db["staffrole"]
arole = db["adminrole"]
infchannel = db["infraction channel"]
appealable = db["Appeal Toggle"]
appealschannel = db["Appeals Channel"]
loa_collection = db["loa"]
loachannel = db["LOA Channel"]
scollection = db["staffrole"]
partnerships = db["Partnerships"]
arole = db["adminrole"]
promochannel = db["promo channel"]
LOARole = db["LOA Role"]
suspensions = db["Suspensions"]
infractiontypes = db["infractiontypes"]
consent = db["consent"]
modules = db["Modules"]
collection = db["infractions"]
Customisation = db["Customisation"]


class VoidInf(discord.ui.Modal, title="Void Infraction"):
    def __init__(self, user, guild, author):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author

    InfractionID = discord.ui.TextInput(
        label="ID",
        placeholder="e.g 20454073",
    )

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        id = self.InfractionID.value
        filter = {"guild_id": interaction.guild.id, "random_string": id}

        infraction = collection.find_one(filter)

        if infraction is None:
            await interaction.response.edit_message(
                content=f"{no} **{interaction.user.display_name}**, I couldn't find the infraction with ID `{id}`.",
                view=Return(self.user, self.guild, self.author),
                embed=None,
                allowed_mentions=discord.AllowedMentions.none()
            )
            return

        collection.update_one(filter, {'$set': {'voided': True}})

        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name}**, I've voided the infraction with ID `{id}`",
            view=Return(self.user, self.guild, self.author),
            embed=None,
            allowed_mentions=discord.AllowedMentions.none()
        )


class LOA(discord.ui.Modal, title="Create Leave Of Absence"):
    def __init__(self, user, guild, author):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author

    Duration = discord.ui.TextInput(
        label="Duration",
        placeholder="e.g 1w (m/h/d/w)",
    )

    reason = discord.ui.TextInput(label="Reason", placeholder="Reason for their loa")

    async def on_submit(self, interaction: discord.Interaction):
        duration = self.Duration.value
        reason = self.reason.value
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        duration_value = int(duration[:-1])
        duration_unit = duration[-1]
        duration_seconds = duration_value

        if duration_unit == "m":
            duration_seconds *= 60
        elif duration_unit == "h":
            duration_seconds *= 3600
        elif duration_unit == "d":
            duration_seconds *= 86400
        elif duration_unit == "w":
            duration_seconds *= 604800

        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)

        data = loachannel.find_one({"guild_id": interaction.guild.id})
        if data:
            channel_id = data["channel_id"]
            channel = interaction.guild.get_channel(channel_id)

            if channel:
                embed = discord.Embed(
                    title=f"LOA Created",
                    description=f"* **User:** {self.user.mention}\n* **Start Date**: <t:{int(start_time.timestamp())}:f>\n* **End Date:** <t:{int(end_time.timestamp())}:f>\n* **Reason:** {self.reason}",
                    color=discord.Color.dark_embed(),
                )
                embed.set_author(
                    icon_url=self.user.display_avatar, name=self.user.display_name
                )
                embed.set_thumbnail(url=self.user.display_avatar)
                loadata = {
                    "guild_id": interaction.guild.id,
                    "user": self.user.id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "reason": reason,
                    "active": True,
                }
                loarole_data = LOARole.find_one({"guild_id": interaction.guild.id})
                if loarole_data:
                    loarole = loarole_data["staffrole"]
                    if loarole:
                        role = discord.utils.get(interaction.guild.roles, id=loarole)
                        if role:
                            try:
                                await self.user.add_roles(role)
                            except discord.Forbidden:
                                await interaction.response.edit_message(
                                    content=f"{no} I don't have permission to add roles.",
                                    view=Return(self.user, self.guild, self.author),
                                    embed=None,
                                )
                                return

                await interaction.response.edit_message(
                    content=f"{tick} Created LOA for **@{self.user.display_name}**",
                    view=Return(self.user, self.guild, self.author),
                    embed=None,
                    allowed_mentions=discord.AllowedMentions.none()
                )
                loa_collection.insert_one(loadata)
                try:
                    await channel.send(
                        f"<:Add:1163095623600447558> LOA was created by **@{interaction.user.display_name}**",
                        embed=embed,
                        
                    )
                except discord.Forbidden:
                    await interaction.response.edit_message(
                        content=f"{no} I don't have permission to view that channel.",
                        view=Return(self.user, self.guild, self.author),
                        embed=None,
                    )
                    return
                try:
                    await self.user.send(
                        f"<:Add:1163095623600447558> A LOA was created for you **@{interaction.guild.name}**",
                        embed=embed,
                        allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False, replied_user=False)
                    )
                except discord.Forbidden:
                    pass


class PromotionRole(discord.ui.RoleSelect):
    def __init__(self, user, guild, author):
        super().__init__(placeholder="Updated Rank")
        self.user = user
        self.guild = guild
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        selected_role_id = self.values[0].id
        role = discord.utils.get(interaction.guild.roles, id=selected_role_id)

        if role is None:
            embed = discord.Embed(
                description=f"Role with ID {selected_role_id} not found.",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if interaction.user.top_role <= role:
            await interaction.response.edit_message(
                content=f"{no} **{interaction.user.display_name}**, you are below the role `{role.name}` and do not have the authority to promote this member.",
                view=Return(self.user, self.guild, self.author),
                embed=None,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        await interaction.response.send_modal(
            PromotionReason(self.user, self.guild, self.author, selected_role_id)
        )


class PromotionReason(discord.ui.Modal, title="Reason"):
    def __init__(self, user, guild, author, role):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author
        self.role = role

    Reason = discord.ui.TextInput(
        label="Reason?",
        placeholder="Whats the reason for the promotion?",
    )

    async def replace_variables(self, message, replacements):
        for placeholder, value in replacements.items():
            if value is not None:
                message = str(message).replace(placeholder, str(value))
            else:
                message = str(message).replace(placeholder, "")
        return message

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view!",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        reason = self.Reason.value
        role = discord.utils.get(interaction.guild.roles, id=self.role)

        consent_data = consent.find_one({"user_id": self.user.id})
        if consent_data is None:
            consent.insert_one(
                {
                    "user_id": self.user.id,
                    "infractionalert": "Enabled",
                    "PromotionAlerts": "Enabled",
                }
            )
            consent_data = {
                "user_id": self.user.id,
                "infractionalert": "Enabled",
                "PromotionAlerts": "Enabled",
            }
        custom = Customisation.find_one(
            {"guild_id": interaction.guild.id, "type": "Promotions"}
        )
        if custom:
            replacements = {
                "{staff.mention}": self.user.mention,
                "{staff.name}": self.user.display_name,
                "{author.mention}": self.author.mention,
                "{author.name}": self.author.display_name,
                "{reason}": reason,
                "{newrank}": role.mention,
            }
            embed_title = await self.replace_variables(custom["title"], replacements)
            embed_description = await self.replace_variables(
                custom["description"], replacements
            )

            embed_author = await self.replace_variables(custom["author"], replacements)
            if custom["thumbnail"] == "{staff.avatar}":
                embed_thumbnail = self.user.display_avatar
            else:
                embed_thumbnail = custom["thumbnail"]

            if custom["author_icon"] == "{author.avatar}":
                authoricon = self.author.display_avatar
            else:
                authoricon = custom["author_icon"]

            if embed_thumbnail == "None":
                embed_thumbnail = None

            if authoricon == "None":
                authoricon = None

            embed = discord.Embed(
                title=embed_title,
                description=embed_description,
                color=int(custom["color"], 16),
            )

            embed.set_thumbnail(url=embed_thumbnail)
            print(str(embed_author))

            if str(embed_author) == "None":
                embed.set_author(name="", icon_url="")
            else:
                embed.set_author(name=embed_author, icon_url=authoricon)
            if custom["image"]:
                embed.set_image(url=custom["image"])

        else:

            embed = discord.Embed(
                title=f"Staff Promotion",
                color=0x2B2D31,
                description=f"* **User:** {self.user.mention}\n* **Updated Rank:** {role.mention}\n* **Reason:** {reason}",
            )
            embed.set_thumbnail(url=self.user.display_avatar)
            embed.set_author(
                name=f"Signed, {self.author.display_name}",
                icon_url=self.author.display_avatar.url,
            )

        guild_id = interaction.guild.id
        data = promochannel.find_one({"guild_id": guild_id})

        if data:
            channel_id = data["channel_id"]
            channel = interaction.guild.get_channel(channel_id)

            if channel:

                try:
                    await self.user.add_roles(role)
                except discord.Forbidden:
                    await interaction.response.edit_message(
                        content=f"<:Allonswarning:1123286604849631355> **{interaction.user.display_name}**, I don't have permission to add roles.",
                        embed=None,
                        view=Return(self.user, self.guild, self.author)
                        , allowed_mentions=discord.AllowedMentions.none()
                    )
                    return

                try:
                    await channel.send(f"{self.user.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False, replied_user=False))
                except discord.Forbidden:
                    await interaction.response.edit_message(
                        content=f"{no} I don't have permission to view that channel.",
                        embed=None,
                        view=Return(self.user, self.guild, self.author),
                    )
                    return

                await interaction.response.edit_message(
                    content=f"{tick} **{self.author.display_name}**, I've promoted **@{self.user.display_name}**",
                    embed=None,
                    view=Return(self.user, self.guild, self.author),
                    allowed_mentions=discord.AllowedMentions.none()
                )

                if consent_data["PromotionAlerts"] == "Enabled":
                    try:
                     await self.user.send(
                        f"🎉 You were promoted **@{interaction.guild.name}!**",
                        embed=embed,
                    )
                    except discord.Forbidden:
                        print('Could not send message to this user')
                        pass 
                else:
                    pass

        else:
            await interaction.response.edit_message(
                content=f"{Warning} **{interaction.user.display_name}**, the channel is not set up. Please run `/config`",
                embed=None,
                view=None,
                allowed_mentions=discord.AllowedMentions.none()
            )


class Reason(discord.ui.Modal, title="Reason"):
    def __init__(self, user, guild, author, option):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author
        self.option = option

    Reason = discord.ui.TextInput(
        label="Reason?",
        placeholder="Whats the reason for the infraction?",
    )

    async def replace_variables(self, message, replacements):
        for placeholder, value in replacements.items():
            if value is not None:
                message = str(message).replace(placeholder, str(value))
            else:
                message = str(message).replace(placeholder, "")
        return message

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view!",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        consent_data = consent.find_one({"user_id": self.user.id})
        if consent_data is None:
            consent.insert_one(
                {
                    "user_id": self.user.id,
                    "infractionalert": "Enabled",
                    "PromotionAlerts": "Enabled",
                }
            )
            consent_data = {
                "user_id": self.user.id,
                "infractionalert": "Enabled",
                "PromotionAlerts": "Enabled",
            }
        random_string = "".join(random.choices(string.digits, k=8))
        reason = self.Reason.value
        custom = Customisation.find_one(
            {"guild_id": interaction.guild.id, "type": "Infractions"}
        )
        if custom:
            replacements = {
                "{staff.mention}": self.user.mention,
                "{staff.name}": self.user.display_name,
                "{author.mention}": self.author.mention,
                "{author.name}": self.author.display_name,
                "{action}": self.option,
                "{reason}": reason,
            }
            embed_title = await self.replace_variables(custom["title"], replacements)
            embed_description = await self.replace_variables(
                custom["description"], replacements
            )

            embed_author = await self.replace_variables(custom["author"], replacements)
            if custom["thumbnail"] == "{staff.avatar}":
                embed_thumbnail = self.user.display_avatar
            else:
                embed_thumbnail = custom["thumbnail"]

            if custom["author_icon"] == "{author.avatar}":
                authoricon = self.author.display_avatar
            else:
                authoricon = custom["author_icon"]

            if embed_thumbnail == "None":
                embed_thumbnail = None

            if authoricon == "None":
                authoricon = None

            if embed_author == None:
                embed_author = ""
            embed = discord.Embed(
                title=embed_title,
                description=embed_description,
                color=int(custom["color"], 16),
            )

            embed.set_thumbnail(url=embed_thumbnail)
            embed.set_author(name=embed_author, icon_url=authoricon)
            embed.set_footer(text=f"Infraction ID | {random_string}")
            if custom["image"]:
                embed.set_image(url=custom["image"])

        else:

            embed = discord.Embed(
                title="Staff Consequences & Discipline",
                description=f"* **Staff Member:** {self.user.mention}\n* **Action:** {self.option}\n* **Reason:** {reason}",
                color=discord.Color.dark_embed(),
            )
            embed.set_thumbnail(url=self.user.display_avatar)
            embed.set_author(
                name=f"Signed, {self.author.display_name}",
                icon_url=self.author.display_avatar,
            )
            embed.set_footer(text=f"Infraction ID | {random_string}")
        infract_data = {
            "management": self.author.id,
            "staff": self.user.id,
            "action": self.option,
            "reason": reason,
            "notes": "`N/A`",
            "random_string": random_string,
            "guild_id": interaction.guild.id,
        }

        guild_id = interaction.guild.id
        data = infchannel.find_one({"guild_id": guild_id})
        if data:
            channel_id = data["channel_id"]
            channel = interaction.guild.get_channel(channel_id)

            if channel:

                try:
                    await channel.send(f"{self.user.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False, replied_user=False))
                except discord.Forbidden:
                    await interaction.response.edit_message(
                        content=f"{no} I don't have permission to view that channel.",
                        view=Return(self.user, self.guild, self.author),
                        embed=None, allowed_mentions=discord.AllowedMentions.none()
                    )
                    return
                await interaction.response.edit_message(
                    content=f"{tick} **{self.author.display_name}**, I've infracted **@{self.user.display_name}**",
                    embed=None,
                    view=Return(self.user, self.guild, self.author)
                    , allowed_mentions=discord.AllowedMentions.none()
                )
                collection.insert_one(infract_data)
                if consent_data["infractionalert"] == "Enabled":
                    try:
                        await self.user.send(
                            f"<:SmallArrow:1140288951861649418> From **{interaction.guild.name}**",
                            embed=embed,
                        )
                    except discord.Forbidden:
                        print('Could not send message to this user')
                        pass
                else:
                    pass
        else:
            await interaction.response.edit_message(
                content=f"{Warning} **{self.author.display_name}**, the channel is not setup please run `/config`",
                embed=None,
                view=Return(self.user, self.guild, self.author),
                allowed_mentions=discord.AllowedMentions.none()
            )


class InfractionOption(discord.ui.Select):
    def __init__(self, user, guild, author):
        self.user = user
        self.guild = guild
        self.author = author
        options = self.get_infraction_types_from_db(guild)
        super().__init__(
            placeholder="Action", min_values=1, max_values=1, options=options
        )

    def get_infraction_types_from_db(self, guild):
        infraction_types = [
            discord.SelectOption(label="Activity Notice"),
            discord.SelectOption(label="Verbal Warning"),
            discord.SelectOption(label="Warning"),
            discord.SelectOption(label="Strike"),
            discord.SelectOption(label="Demotion"),
            discord.SelectOption(label="Termination"),
        ]

        existing_types = set(option.label for option in infraction_types)
        additional_types = []

        typeresult = infractiontypes.find_one({"guild_id": guild.id})
        if typeresult:
            additional_types = typeresult["types"]

        for infraction_type in additional_types:
            if infraction_type not in existing_types:
                infraction_types.append(discord.SelectOption(label=infraction_type))

        return infraction_types

    async def callback(self, interaction: discord.Interaction):
        option = self.values[0]
        await interaction.response.send_modal(
            Reason(self.user, self.guild, self.author, option)
        )


class InfractionOptionView(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author
        self.add_item(InfractionOption(self.user, self.guild, self.author))


class PromotionRoleView(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author
        self.add_item(PromotionRole(self.user, self.guild, self.author))


class LOACreation(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author
        self.add_item(LOA(self.user, self.guild, self.author))


class AdminPanelCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.hybrid_group(name="admin")
    async def admin(self, ctx):
        pass

    @admin.command(description="Manage a staff member.")
    async def panel(self, ctx, staff: discord.Member):
        if not await has_admin_role(ctx):
            return

        infractions = collection.count_documents(
            {"staff": staff.id, "guild_id": ctx.guild.id, "action": {"$ne": "Demotion"}}
        )
        demotions = collection.count_documents(
            {"staff": staff.id, "guild_id": ctx.guild.id, "action": "Demotion"}
        )
        loa = loa_collection.find_one(
            {"user": staff.id, "guild_id": ctx.guild.id, "active": True}
        )
        loasmg = ""
        if loa is None:
            loamsg = "False"
        else:
            loamsg = "True"

        embed = discord.Embed(
            title=f"Admin Panel - {staff.name}",
            description=f"**Mention:** {staff.mention}\n**ID:** *{staff.id}* ",
            timestamp=datetime.now(),
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="<:data:1166529224094523422> Staff Data",
            value=f"<:arrow:1166529434493386823>**Infractions:** {infractions}\n<:arrow:1166529434493386823>**Demotions:** {demotions}\n<:arrow:1166529434493386823>**Leave Of Absence:** {loamsg}",
        )
        embed.set_author(name=staff.name, icon_url=staff.display_avatar)
        embed.set_footer(
            text="Staff Management Panel",
            icon_url="https://media.discordapp.net/ephemeral-attachments/1139907646963597423/1187454549099806811/1154092651193323661.png?ex=6596f23a&is=65847d3a&hm=289bd45a9c6779853b2a78d7848636433e8aa63173781aec51447c25f8a06453&=",
        )
        embed.set_thumbnail(url=staff.display_avatar)
        embed.set_image(
            url="https://astrobirb.dev/assets/img/logos/invisible.png"
        )
        view = AdminPanel(staff, ctx.guild, ctx.author)
        await ctx.send(embed=embed, view=view)

    async def acheck(self, ctx, staff):
        filter = {"guild_id": ctx.guild.id}
        staff_data = arole.find_one(filter)

        if staff_data and "staffrole" in staff_data:
            staff_role_ids = staff_data["staffrole"]

            if not isinstance(staff_role_ids, list):
                staff_role_ids = [staff_role_ids]

            staff_roles = [role.id for role in staff.roles]
            if any(role_id in staff_roles for role_id in staff_role_ids):
                return True

        return False

    @admin.command(description="View an admins stats")
    async def stats(self, ctx, user: discord.Member = None):
        await ctx.defer()
        if not await has_admin_role(ctx):
            return
        if user is None:
            user = ctx.author
        has_a_role = await self.acheck(ctx, user)
        if not has_a_role:
            await ctx.send(
                f"{no} **{ctx.author.display_name},** **@{user.display_name}** is not a admin.",
                ephemeral=True,
            )
            return
        partnershipscount = partnerships.count_documents(
            {"admin": user.id, "guild_id": ctx.guild.id}
        )
        infractioncount = collection.count_documents(
            {"staff": user.id, "guild_id": ctx.guild.id}
        )
        demotioncount = collection.count_documents(
            {"staff": user.id, "guild_id": ctx.guild.id, "action": "Demotion"}
        )
        suspensioncount = suspensions.count_documents(
            {"management": user.id, "guild_id": ctx.guild.id}
        )

        embed = discord.Embed(
            title=f"<:stats:1199023533938970827> {ctx.author.display_name}'s Stats",
            description=f"",
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="<:Infraction:1162134605885870180> Punishments",
            value=f">>> **Infractions Logged:** {infractioncount}\n**Demotions Logged:** {demotioncount}\n**Suspensions Logged:** {suspensioncount}",
            inline=False,
        )
        embed.add_field(
            name="<:Partner:1162135285031772300> Partnerships",
            value=f">>> **Partnerships Logged:** {partnershipscount}",
            inline=False,
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        embed.set_thumbnail(url=user.display_avatar)
        view = IssuedInfraction(user, ctx.author, ctx)
        await ctx.send(embed=embed, view=view)


class IssuedInfraction(discord.ui.View):
    def __init__(self, user, author, ctx):
        super().__init__()
        self.user = user
        self.author = author
        self.ctx = ctx

    async def InfractionModuleCheck(self, ctx):
        modulesdata = modules.find_one({"guild_id": ctx.guild.id})
        if modulesdata is None:
            return False
        elif modulesdata["infractions"] == True:
            return True

    @discord.ui.button(
        label="View Issued Infractions",
        style=discord.ButtonStyle.grey,
        emoji="<:infractionssearch:1200479190118576158>",
    )
    async def InfractionsView(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view.",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if not await self.InfractionModuleCheck(interaction):
            await interaction.response.send_message(
                f"{no} **{interaction.user.display_name}**, this module is currently disabled.",
                ephemeral=True,
            )
            return

        filter = {
            "guild_id": interaction.guild.id,
            "management": self.user.id,
        }

        infractions = collection.find(filter)
        embeds = []
        infraction_list = []

        for infraction in infractions:
            infraction_info = {
                "id": infraction["random_string"],
                "action": infraction["action"],
                "reason": infraction["reason"],
                "notes": infraction["notes"],
                "staff": infraction["staff"],
            }

            infraction_list.append(infraction_info)

        if not infraction_list:
            await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name}**, there are no infractions issued by this user.",
                ephemeral=True,
            )
            return

        for idx, infraction_info in enumerate(infraction_list):
            if idx % 9 == 0:
                embed = discord.Embed(
                    title=f"{self.user.name}'s Issued Infractions",
                    description=f"* **User:** {self.user.mention}\n* **User ID:** {self.user.id}",
                    color=discord.Color.dark_embed(),
                )
                embed.set_thumbnail(url=self.user.display_avatar)
                embed.set_author(
                    icon_url=self.user.display_avatar, name=self.user.display_name
                )

            embed.add_field(
                name=f"<:Document:1166803559422107699> Infraction | {infraction_info['id']}",
                value=f"<:arrow:1166529434493386823>**Infracted User:** <@{infraction_info['staff']}>\n<:arrow:1166529434493386823>**Action:** {infraction_info['action']}\n<:arrow:1166529434493386823>**Reason:** {infraction_info['reason']}\n<:arrow:1166529434493386823>**Notes:** {infraction_info['notes']}",
                inline=False,
            )

            if (idx + 1) % 9 == 0 or idx == len(infraction_list) - 1:
                embeds.append(embed)

        PreviousButton = discord.ui.Button(label="<")
        NextButton = discord.ui.Button(label=">")
        FirstPageButton = discord.ui.Button(label="<<")
        LastPageButton = discord.ui.Button(label=">>")
        InitialPage = 0
        timeout = 42069

        paginator = Paginator.Simple(
            PreviousButton=PreviousButton,
            NextButton=NextButton,
            FirstEmbedButton=FirstPageButton,
            LastEmbedButton=LastPageButton,
            InitialPage=InitialPage,
            timeout=timeout,
        )

        await paginator.start(self.ctx, pages=embeds)
        button.disabled = True
        await interaction.response.edit_message(view=self)


class AdminPanel(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author

    async def InfractionModuleCheck(self, ctx):
        modulesdata = modules.find_one({"guild_id": ctx.guild.id})
        if modulesdata is None:
            return False
        elif modulesdata["infractions"] == True:
            return True

    async def PromotionModuleCheck(self, ctx):
        modulesdata = modules.find_one({"guild_id": ctx.guild.id})
        if modulesdata is None:
            return False
        elif modulesdata["Promotions"] == True:
            return True

    async def LOAModuleCheck(self, ctx):
        modulesdata = modules.find_one({"guild_id": ctx.guild.id})
        if modulesdata is None:
            return False
        elif modulesdata["LOA"] == True:
            return True

    @discord.ui.button(
        label="Promote",
        style=discord.ButtonStyle.grey,
        emoji="<:Promotion:1162134864594735315>",
    )
    async def Promote(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view!",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if not await self.PromotionModuleCheck(interaction):
            await interaction.response.send_message(
                f"{no} **{interaction.user.display_name}**, this module is currently disabled.",
                ephemeral=True,
            )
            return
        if self.author == self.user:
            await interaction.response.send_message(
                f"{no} You can't promote yourself.", ephemeral=True
            )
            return

        view = Return(self.user, self.guild, self.author)
        view.add_item(PromotionRole(self.user, self.guild, self.author))
        await interaction.response.edit_message(view=view)
        
    @discord.ui.button(
        label="Infract",
        style=discord.ButtonStyle.grey,
        emoji="<:Infraction:1162134605885870180>",
    )
    async def Infract(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):

        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view!",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if not await self.InfractionModuleCheck(interaction):
            await interaction.response.send_message(
                f"{no} **{interaction.user.display_name}**, this module is currently disabled.",
                ephemeral=True,
            )
            return
        if self.author == self.user:
            await interaction.response.send_message(
                f"{no} You can't infract yourself.", ephemeral=True
            )
            return

        view = Return(self.user, self.guild, self.author)
        view.add_item(InfractionOption(self.user, self.guild, self.author))
        await interaction.response.edit_message(view=view)

    @discord.ui.button(
        label="Search",
        style=discord.ButtonStyle.grey,
        emoji="<:Search:1166509265951932546>",
    )
    async def Search(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view.",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if not await self.InfractionModuleCheck(interaction):
            await interaction.response.send_message(
                f"{no} **{interaction.user.display_name}**, this module is currently disabled.",
                ephemeral=True,
            )
            return
        print(
            f"Searching infractions for staff ID: {self.user.id} in guild ID: {self.user.guild.id}"
        )

        filter = {
            "guild_id": interaction.guild.id,
            "staff": self.user.id,
        }

        infractions = collection.find(filter)

        infraction_list = []

        for infraction in infractions[:15]:
            infraction_info = {
                "id": infraction["random_string"],
                "action": infraction["action"],
                "reason": infraction["reason"],
                "notes": infraction["notes"],
                "management": infraction["management"],
                "jump_url": (
                    infraction["jump_url"] if "jump_url" in infraction else "N/A"
                ),
                "expiration": (
                    infraction["expiration"] if "expiration" in infraction else "N/A"
                ),
                "expired": infraction["expired"] if "expired" in infraction else "N/A",
                "voided": infraction["voided"] if "voided" in infraction else "N/A",
            }

            infraction_list.append(infraction_info)

        if not infraction_list:
            await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name}**, there are no infractions found for **@{self.user.display_name}**.",
                ephemeral=True,
            )
            return

        print(f"Found {len(infraction_list)} infractions for {self.user.display_name}")

        embed = discord.Embed(
            title=f"{self.user.name}'s Infractions",
            description=f"* **User:** {self.user.mention}\n* **User ID:** {self.user.id}",
            color=discord.Color.dark_embed(),
        )
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.set_author(icon_url=self.user.display_avatar, name=self.user.display_name)

        for infraction_info in infraction_list:

            if infraction_info["jump_url"] == "N/A":
                jump_url = ""
            else:
                jump_url = f"\n<:arrow:1166529434493386823>**[Jump to Infraction]({infraction_info['jump_url']})**"

            if infraction_info["expiration"] == "N/A":
                expiration = ""
            else:
                expiration = f"\n<:arrow:1166529434493386823>**Expiration:** <t:{int(infraction_info['expiration'].timestamp())}:D>"
                if infraction_info["expiration"] < datetime.now():
                    expiration = f"\n<:arrow:1166529434493386823>**Expiration:** <t:{int(infraction_info['expiration'].timestamp())}:D> **(Infraction Expired)**"
            management = f"<@{infraction_info['management']}>"
            embed.add_field(
                name=f"<:Document:1166803559422107699> Infraction | {infraction_info['id']}",
                value=f"<:arrow:1166529434493386823>**Infracted By:** {management}\n<:arrow:1166529434493386823>**Action:** {infraction_info['action']}\n<:arrow:1166529434493386823>**Reason:** {infraction_info['reason']}\n<:arrow:1166529434493386823>**Notes:** {infraction_info['notes']}{expiration}{jump_url}",
                inline=False,
            )

        view = RevokeInfraction(self.user, interaction.guild, self.author)
        await interaction.response.edit_message(embed=embed, view=view, content=None)

    @discord.ui.button(
        label="LOA", style=discord.ButtonStyle.grey, emoji="<:LOA:1164969910238203995>"
    )
    async def LOA(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your view.",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if not await self.LOAModuleCheck(interaction):
            await interaction.response.send_message(
                f"{no} **{interaction.user.display_name}**, this module is currently disabled.",
                ephemeral=True,
            )
            return
        loa = loa_collection.find_one(
            {"user": self.user.id, "guild_id": interaction.guild.id, "active": True,  'request': {'$ne': True}}
        )
        loainactive = loa_collection.find(
            {"user": self.user.id, "guild_id": interaction.guild.id, "active": False,  'request': {'$ne': True}}
        )
        view = None

        if loa is None:
            description = []
            for request in loainactive:
                start_time = request["start_time"]
                end_time = request["end_time"]
                reason = request["reason"]
                description.append(
                    f"<:LOA:1164969910238203995> **Previous LOA**\n<:arrow:1166529434493386823><t:{int(start_time.timestamp())}:f> - <t:{int(end_time.timestamp())}:f> • {reason}"
                )

            embed = discord.Embed(
                title="Leave Of Absense",
                description=f"\n".join(description),
                color=discord.Color.dark_embed(),
            )
            embed.set_thumbnail(url=self.user.display_avatar)
            embed.set_author(
                icon_url=self.user.display_avatar, name=self.user.display_name
            )
            view = LOACreate(self.user, interaction.guild, self.author)

        else:
            start_time = loa["start_time"]
            end_time = loa["end_time"]
            reason = loa["reason"]

            embed = discord.Embed(
                title=f"Leave Of Absence",
                color=discord.Color.dark_embed(),
                description=f"<:LOA:1164969910238203995> **Active LOA**\n<:arrow:1166529434493386823>**Start Date:** <t:{int(start_time.timestamp())}:f>\n<:arrow:1166529434493386823>**End Date:** <t:{int(end_time.timestamp())}:f>\n<:arrow:1166529434493386823>**Reason:** {reason}",
            )
            embed.set_thumbnail(url=self.user.display_avatar)
            embed.set_author(
                icon_url=self.user.display_avatar, name=self.user.display_name
            )

            view = LOAPanel(self.user, interaction.guild, self.author)

        await interaction.response.edit_message(embed=embed, view=view, content=None)


class Return(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author

    @discord.ui.button(
        label="Return",
        style=discord.ButtonStyle.grey,
        emoji="<:Return:1166514220960063568>",
        row=2
    )
    async def Return77(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view!",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        infractions = collection.count_documents(
            {
                "staff": self.user.id,
                "guild_id": interaction.guild.id,
                "action": {"$ne": "Demotion"},
            }
        )
        demotions = collection.count_documents(
            {
                "staff": self.user.id,
                "guild_id": interaction.guild.id,
                "action": "Demotion",
            }
        )
        loa = loa_collection.find_one(
            {"user": self.user.id, "guild_id": interaction.guild.id, "active": True}
        )
        loasmg = ""
        if loa:
            loamsg = "True"
        else:
            loamsg = "False"
        embed = discord.Embed(
            title=f"Admin Panel - {self.user.name}",
            description=f"**Mention:** {self.user.mention}\n**ID:** *{self.user.id}* ",
            timestamp=datetime.now(),
            color=discord.Color.dark_embed(),
        )
        embed.set_author(name=self.user.name, icon_url=self.user.display_avatar)
        embed.set_footer(
            text="Staff Management Panel",
            icon_url="https://media.discordapp.net/ephemeral-attachments/1140411707953520681/1165221940722675722/1035353776460152892.png?ex=6546107f&is=65339b7f&hm=8d73392705483a84a47d09a7cd4838cd2e1235caa1022f10777ea1fec4a91f13&=",
        )
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.add_field(
            name="<:data:1166529224094523422> Staff Data",
            value=f"<:arrow:1166529434493386823>**Infractions:** {infractions}\n<:arrow:1166529434493386823>**Demotions:** {demotions}\n<:arrow:1166529434493386823>**Leave Of Absence:** {loamsg}",
        )
        view = AdminPanel(self.user, interaction.guild, self.author)
        embed.set_image(
            url="https://astrobirb.dev/assets/img/logos/invisible.png"
        )
        await interaction.response.edit_message(embed=embed, view=view, content=None)


class LOAPanel(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author

    @discord.ui.button(
        label="Void LOA",
        style=discord.ButtonStyle.grey,
        custom_id="persistent_view:cancel",
        emoji="<:Exterminate:1164970632262451231>",
    )
    async def End(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.user
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view!",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        loa = loa_collection.find_one(
            {"user": self.user.id, "guild_id": interaction.guild.id, "active": True}
        )
        loarole_data = LOARole.find_one({"guild_id": interaction.guild.id})
        if loarole_data:
            loarole = loarole_data["staffrole"]
            if loarole:
                role = discord.utils.get(interaction.guild.roles, id=loarole)
                if role:
                    try:
                        await user.remove_roles(role)
                    except discord.Forbidden:
                        await interaction.response.edit_message(
                            content=f"{no} I don't have permission to remove roles.",
                            view=Return(self.user, self.guild, self.author),
                            embed=None,
                        )
                        return
        try:
            await user.send(
                f"<:bin:1160543529542635520> Your LOA **@{self.guild.name}** has been voided."
            )
        except discord.Forbidden:
            pass

        loa_collection.update_many(
            {"guild_id": interaction.guild.id, "user": user.id},
            {"$set": {"active": False}},
        )

        await interaction.response.edit_message(
            embed=None,
            content=f"{tick} Succesfully ended **@{user.display_name}'s** LOA", allowed_mentions=discord.AllowedMentions.none(),
            view=Return(self.user, self.guild, self.author),
        )

    @discord.ui.button(
        label="Return",
        style=discord.ButtonStyle.grey,
        emoji="<:Return:1166514220960063568>",
    )
    async def Return2(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view!",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        infractions = collection.count_documents(
            {
                "staff": self.user.id,
                "guild_id": interaction.guild.id,
                "action": {"$ne": "Demotion"},
            }
        )
        demotions = collection.count_documents(
            {
                "staff": self.user.id,
                "guild_id": interaction.guild.id,
                "action": "Demotion",
            }
        )
        loa = loa_collection.find_one(
            {"user": self.user.id, "guild_id": interaction.guild.id, "active": True}
        )
        loasmg = ""
        if loa:
            loamsg = "True"
        else:
            loamsg = "False"
        embed = discord.Embed(
            title=f"Admin Panel - {self.user.name}",
            description=f"**Mention:** {self.user.mention}\n**ID:** *{self.user.id}* ",
            timestamp=datetime.now(),
            color=discord.Color.dark_embed(),
        )
        embed.set_author(name=self.user.name, icon_url=self.user.display_avatar)
        embed.set_footer(
            text="Staff Management Panel",
            icon_url="https://media.discordapp.net/ephemeral-attachments/1140411707953520681/1165221940722675722/1035353776460152892.png?ex=6546107f&is=65339b7f&hm=8d73392705483a84a47d09a7cd4838cd2e1235caa1022f10777ea1fec4a91f13&=",
        )
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.add_field(
            name="<:data:1166529224094523422> Staff Data",
            value=f"<:arrow:1166529434493386823>**Infractions:** {infractions}\n<:arrow:1166529434493386823>**Demotions:** {demotions}\n<:arrow:1166529434493386823>**Leave Of Absence:** {loamsg}",
        )
        view = AdminPanel(self.user, interaction.guild, self.author)
        embed.set_image(
            url="https://astrobirb.dev/assets/img/logos/invisible.png"
        )
        await interaction.response.edit_message(embed=embed, view=view, content=None)


class LOACreate(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author

    @discord.ui.button(
        label="Create Leave Of Absence",
        style=discord.ButtonStyle.grey,
        custom_id="persistent_view:cancel",
        emoji="<:Add:1163095623600447558>",
    )
    async def CreateLOA(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view!",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.send_modal(LOA(self.user, self.guild, self.author))

    @discord.ui.button(
        label="Return",
        style=discord.ButtonStyle.grey,
        emoji="<:Return:1166514220960063568>",
    )
    async def Return3(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view!",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        infractions = collection.count_documents(
            {
                "staff": self.user.id,
                "guild_id": interaction.guild.id,
                "action": {"$ne": "Demotion"},
            }
        )
        demotions = collection.count_documents(
            {
                "staff": self.user.id,
                "guild_id": interaction.guild.id,
                "action": "Demotion",
            }
        )
        loa = loa_collection.find_one(
            {"user": self.user.id, "guild_id": interaction.guild.id, "active": True}
        )
        loasmg = ""
        if loa:
            loamsg = "True"
        else:
            loamsg = "False"
        embed = discord.Embed(
            title=f"Admin Panel - {self.user.name}",
            description=f"**Mention:** {self.user.mention}\n**ID:** *{self.user.id}* ",
            timestamp=datetime.now(),
            color=discord.Color.dark_embed(),
        )
        embed.set_author(name=self.user.name, icon_url=self.user.display_avatar)
        embed.set_footer(
            text="Staff Management Panel",
            icon_url="https://media.discordapp.net/ephemeral-attachments/1140411707953520681/1165221940722675722/1035353776460152892.png?ex=6546107f&is=65339b7f&hm=8d73392705483a84a47d09a7cd4838cd2e1235caa1022f10777ea1fec4a91f13&=",
        )
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.add_field(
            name="<:data:1166529224094523422> Staff Data",
            value=f"<:arrow:1166529434493386823>**Infractions:** {infractions}\n<:arrow:1166529434493386823>**Demotions:** {demotions}\n<:arrow:1166529434493386823>**Leave Of Absence:** {loamsg}",
        )
        view = AdminPanel(self.user, interaction.guild, self.author)
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png"
        )
        await interaction.response.edit_message(embed=embed, view=view, content=None)


class RevokeInfraction(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author

    @discord.ui.button(
        label="Void Infraction",
        style=discord.ButtonStyle.grey,
        emoji="<:bin:1160543529542635520>",
    )
    async def InfractionRevoke(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view!",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if self.author == self.user:
            await interaction.response.send_message(
                f"{no} You can't revoke your own infraction.", ephemeral=True
            )
            return

        await interaction.response.send_modal(
            VoidInf(self.user, interaction.guild, self.author)
        )

    @discord.ui.button(
        label="Return",
        style=discord.ButtonStyle.grey,
        emoji="<:Return:1166514220960063568>",
    )
    async def Return3(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view!",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        infractions = collection.count_documents(
            {
                "staff": self.user.id,
                "guild_id": interaction.guild.id,
                "action": {"$ne": "Demotion"},
            }
        )
        demotions = collection.count_documents(
            {
                "staff": self.user.id,
                "guild_id": interaction.guild.id,
                "action": "Demotion",
            }
        )
        loa = loa_collection.find_one(
            {"user": self.user.id, "guild_id": interaction.guild.id, "active": True}
        )
        loasmg = ""
        if loa:
            loamsg = "True"
        else:
            loamsg = "False"
        embed = discord.Embed(
            title=f"Admin Panel - {self.user.name}",
            description=f"**Mention:** {self.user.mention}\n**ID:** *{self.user.id}* ",
            timestamp=datetime.now(),
            color=discord.Color.dark_embed(),
        )
        embed.set_author(name=self.user.name, icon_url=self.user.display_avatar)
        embed.set_footer(
            text="Staff Management Panel",
            icon_url="https://media.discordapp.net/ephemeral-attachments/1140411707953520681/1165221940722675722/1035353776460152892.png?ex=6546107f&is=65339b7f&hm=8d73392705483a84a47d09a7cd4838cd2e1235caa1022f10777ea1fec4a91f13&=",
        )
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.add_field(
            name="<:data:1166529224094523422> Staff Data",
            value=f"<:arrow:1166529434493386823>**Infractions:** {infractions}\n<:arrow:1166529434493386823>**Demotions:** {demotions}\n<:arrow:1166529434493386823>**Leave Of Absence:** {loamsg}",
        )
        view = AdminPanel(self.user, interaction.guild, self.author)
        embed.set_image(
            url="https://astrobirb.dev/assets/img/logos/invisible.png"
        )
        await interaction.response.edit_message(embed=embed, view=view, content=None)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(AdminPanelCog(client))
