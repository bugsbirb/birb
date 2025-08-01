import discord
from utils.emojis import *
from datetime import datetime, timedelta
from utils.ui import BasicPaginator
from utils.format import IsSeperateBot


class QuotaOptions(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Quota Amount", emoji="<:uilsortamountup:1248315081154887761>"
                ),
                discord.SelectOption(
                    label="Role Quota", emoji="<:RoleQuota:1400797914011271231>"
                ),
                discord.SelectOption(
                    label="Ignored Channels", emoji="<:tag:1234998802948034721>"
                ),
                discord.SelectOption(
                    label="Auto Activity", emoji="<:suspensions:1234998406938755122>"
                ),
            ]
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(
                embed=discord.Embed(
                    description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                    color=discord.Colour.brand_red(),
                ),
                ephemeral=True,
            )

        selection = self.values[0]
        view = discord.ui.View()
        if selection == "Quota Amount":
            await interaction.response.send_modal(
                MessageQuota(
                    author=interaction.user, default=None, message=interaction.message
                )
            )
            return
        if selection == "Role By Quota":
            embeds = []
            config = await interaction.client.db["Config"].find_one(
                {"_id": interaction.guild.id}
            )
            roles = config.get("Message Quota", {}).get("Roles", [])
            pages = [roles[i : i + 5] for i in range(0, len(roles), 5)]

            def Embed():
                embed = discord.Embed(color=discord.Color.dark_embed())
                embed.set_author(
                    icon_url="https://cdn.discordapp.com/emojis/1400797914011271231.webp?size=96",
                    name="Role Quotas",
                )
                embed.description = ""
                return embed

            for P in pages:
                embed = Embed()
                for E in P:
                    Role = interaction.guild.get_role(E.get("ID"))
                    if not Role:
                        continue
                    embed.description += f"> {Role.mention} • {E.get('Quota')} messages"
                embeds.append(embed)
            if not embeds:
                embed = Embed()
                embed.description = "-# There are no set role quotas."
                embeds.append(embed)

            RoleManage = RoleQuotaCreation(interaction.user)
            view = BasicPaginator(author=interaction.user, embeds=embeds)
            if IsSeperateBot():
                RoleManage.Add.label = "Add"
                RoleManage.Remove.label = "Remove"
            for item in RoleManage.children:
                view.add_item(item)

            await interaction.response.send_message(
                view=view, embed=embeds[0], ephemeral=True
            )

            return
        if selection == "Ignored Channels":
            Config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            if not Config:
                Config = {"Message Quota": {}, "_id": interaction.guild.id}
            view.add_item(
                IgnoredChannels(
                    author=interaction.user,
                    default=[
                        interaction.guild.get_channel(int(channel_id))
                        for channel_id in Config.get("Message Quota", {}).get(
                            "Ignored Channels", []
                        )
                    ],
                    message=interaction.message,
                ),
            )
            await interaction.response.send_message(view=view, ephemeral=True)
        if selection == "Auto Activity":
            view.add_item(AutoActivity(interaction.user))
            await interaction.response.send_message(view=view, ephemeral=True)


class IgnoredChannels(discord.ui.ChannelSelect):
    def __init__(self, author: discord.Member, default: list = None, message=None):
        super().__init__(
            max_values=10,
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author
        self.default = default
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(
                embed=discord.Embed(
                    description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                    color=discord.Colour.brand_red(),
                ),
                ephemeral=True,
            )

        Config = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        ) or {
            "Message Quota": {"Ignored Channels": []},
            "_id": interaction.guild.id,
        }
        if not Config.get("Message Quota"):
            Config = {
                "Message Quota": {"Ignored Channels": []},
            }

        if "Ignored Channels" not in Config.get("Message Quota"):
            Config["Message Quota"]["Ignored Channels"] = []

        Config["Message Quota"]["Ignored Channels"] = [
            ch_id
            for ch_id in Config["Message Quota"]["Ignored Channels"]
            if ch_id in [channel.id for channel in self.values]
        ] + [
            channel.id
            for channel in self.values
            if channel.id not in Config["Message Quota"]["Ignored Channels"]
        ]

        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": Config}, upsert=True
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )
        view = discord.ui.View()
        view.add_item(QuotaOptions(interaction.user))
        await interaction.response.edit_message(view=view)
        try:
            await self.message.edit(
                embed=await MessageQuotaEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                )
            )
        except:
            pass


# TODO: {"Message Quota": {"Roles": [{"ID": Num, "Quota": 1}, ... etc]}}


class RoleQuotaCreation(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(
        emoji="<:Add:1163095623600447558>", style=discord.ButtonStyle.gray, row=2
    )
    async def Add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                    color=discord.Colour.brand_red(),
                ),
                ephemeral=True,
            )
        view = discord.ui.View()
        view.add_item(RoleQuotaSelect(interaction.user))
        embed = discord.Embed(
            color=discord.Color.dark_embed(),
            description="Select a role to add a custom quota to.",
        )
        await interaction.response.edit_message(view=view, embed=embed)

    @discord.ui.button(
        emoji="<:Subtract:1229040262161109003>", style=discord.ButtonStyle.gray, row=2
    )
    async def Remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(
                embed=discord.Embed(
                    description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                    color=discord.Colour.brand_red(),
                ),
                ephemeral=True,
            )

        config = await interaction.client.db["Config"].find_one(
            {"_id": interaction.guild.id}
        )
        if (
            not config
            or "Message Quota" not in config
            or "Roles" not in config["Message Quota"]
        ):
            return await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name},** there aren't any roles to delete."
            )
        roles = config["Message Quota"]["Roles"]
        if not roles:
            return await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name},** there aren't any roles to delete.",
                ephemeral=True,
            )
        options = [
            discord.SelectOption(
                label=(
                    interaction.guild.get_role(role["ID"]).name
                    if interaction.guild.get_role(role["ID"])
                    else f"Unknown Role ({role['ID']})"
                ),
                value=str(role["ID"]),
            )
            for role in roles
        ]
        view = discord.ui.View()
        view.add_item(RoleQuotaDelete(options=options, author=self.author))
        await interaction.edit_original_response(
            view=view,
            embed=discord.Embed(
                description="Select the role(s) you want to remove the quota for.",
                color=discord.Color.dark_embed(),
            ),
        )


class RoleQuotaSelect(discord.ui.RoleSelect):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(
                embed=discord.Embed(
                    description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                    color=discord.Colour.brand_red(),
                ),
                ephemeral=True,
            )
        await interaction.response.send_modal(
            RoleQuotaModal(author=interaction.user, Role=self.values[0])
        )


class RoleQuotaModal(discord.ui.Modal):
    def __init__(self, author: discord.Member, Role: discord.Role):
        super().__init__(title="Role Quota")
        self.author = author
        self.Role = Role
        self.RoleQuota = discord.ui.TextInput(
            label="Quota", placeholder="What should the quota be for this role?"
        )
        self.add_item(self.RoleQuota)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(
                embed=discord.Embed(
                    description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                    color=discord.Colour.brand_red(),
                ),
                ephemeral=True,
            )
        config = await interaction.client.db["Message Quota"].find_one(
            {"_id": interaction.guild.id}
        )
        if not config:
            config = {"_id": interaction.guild.id, "Message Quota": {"Roles": []}}
        elif "Message Quota" not in config:
            config["Message Quota"] = {"Roles": []}
        elif "Roles" not in config["Message Quota"]:
            config["Message Quota"]["Roles"] = []

        roles: list = config["Message Quota"]["Roles"]

        for Data in roles:
            if Data["ID"] == self.Role.id:
                Data["Quota"] = self.RoleQuota.value
                break
        else:
            roles.append({"ID": self.Role.id, "Quota": self.RoleQuota.value})

        await interaction.client.db["Config"].update_one(
            {"_id": interaction.guild.id}, {"$set": config}, upsert=True
        )
        await interaction.response.edit_message(
            view=None,
            content=f"{tick} **{interaction.user.display_name},** successfully added the role quota.",
            embed=None,
        )


class RoleQuotaDelete(discord.ui.Select):
    def __init__(self, options: list, author: discord.Member):
        super().__init__(options=options, max_values=len(options))
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(
                embed=discord.Embed(
                    description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                    color=discord.Colour.brand_red(),
                ),
                ephemeral=True,
            )

        config = await interaction.client.db["Config"].find_one(
            {"_id": interaction.guild.id}
        )
        if (
            not config
            or "Message Quota" not in config
            or "Roles" not in config["Message Quota"]
        ):
            return await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name},** there aren't any roles to delete."
            )

        roles = config["Message Quota"]["Roles"]
        Roles = [r for r in roles if str(r["ID"]) not in self.values]
        config["Message Quota"]["Roles"] = Roles

        await interaction.client.db["Config"].update_one(
            {"_id": interaction.guild.id}, {"$set": config}, upsert=True
        )
        await interaction.response.edit_message(
            view=None,
            content=f"{tick} **{interaction.user.display_name},** successfully deleted the role quota.",
            embed=None,
        )


class MessageQuota(discord.ui.Modal, title="Message Quota"):
    def __init__(self, author: discord.Member, default: str = None, message=None):
        super().__init__()
        self.Quota = discord.ui.TextInput(
            label="Quota Amount",
            placeholder="Enter the amount of messages required to be active",
            style=discord.TextStyle.short,
            default=default,
        )
        self.add_item(self.Quota)
        self.author = author
        self.message = message

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            Config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            if not Config:
                Config = {"Message Quota": {}, "_id": interaction.guild.id}
            if not Config.get("Message Quota"):
                Config["Message Quota"] = {}
            Config["Message Quota"]["quota"] = int(self.Quota.value)
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$set": Config}, upsert=True
            )
            Updated = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            await interaction.response.edit_message(content="")
            try:
                await self.message.edit(
                    embed=await MessageQuotaEmbed(
                        interaction,
                        Updated,
                        discord.Embed(color=discord.Color.dark_embed()),
                    ),
                )
            except:
                pass
        except ValueError:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** please enter a valid number.",
                color=discord.Colour.brand_red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class AutoActivity(discord.ui.Select):
    def __init__(self, author):
        self.author = author

        options = [
            discord.SelectOption(label="Toggle", emoji="<:Button:1223063359184830494>"),
            discord.SelectOption(label="Channel", emoji="<:tag:1234998802948034721>"),
            discord.SelectOption(
                label="Post Date", emoji="<:time:1158064756104630294>"
            ),
        ]
        super().__init__(
            placeholder="Auto Activity", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        view = discord.ui.View()
        if selection == "Toggle":

            view.add_item(ActivityToggle(interaction.user))
            await interaction.response.send_message(view=view, ephemeral=True)
        if selection == "Channel":
            view.add_item(PostChannel(interaction.user))
            await interaction.response.send_message(view=view, ephemeral=True)
        if selection == "Post Date":
            await interaction.response.send_modal(PostDate())


class PostDate(discord.ui.Modal, title="How often?"):

    postdate = discord.ui.TextInput(
        label="Post Day",
        placeholder="What day do you want it to post every week? (Monday, Tuesday etc)",
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction):
        days = [
            "sunday",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "tuesday",
        ]
        specified_day = self.postdate.value.lower()

        if specified_day not in days:
            await interaction.response.send_message(
                "Invalid day specified. Please enter a valid day of the week.",
                ephemeral=True,
            )
            return
        CurrentDay = datetime.utcnow().weekday()
        Specified = days.index(specified_day)

        Days = (Specified - CurrentDay) % 7

        if Days <= 0:
            Days += 7
        NextDate = datetime.utcnow() + timedelta(days=Days - 1)
        await interaction.client.db["auto activity"].update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"day": self.postdate.value, "nextdate": NextDate}},
            upsert=True,
        )
        embed = discord.Embed(
            title="Success!",
            color=discord.Color.brand_green(),
            description=f"**Next Post Date:** <t:{int(NextDate.timestamp())}>",
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class PostChannel(discord.ui.ChannelSelect):
    def __init__(self, author):
        super().__init__(
            placeholder="Post Channel",
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer(ephemeral=True)

        filter = {"guild_id": interaction.guild.id}
        try:
            await interaction.client.db["auto activity"].update_one(
                filter,
                {"$set": {"channel_id": self.values[0].id if self.values else None}},
                upsert=True,
            )
            await interaction.edit_original_response(content=None)
        except Exception as e:
            return


class ActivityToggle(discord.ui.Select):
    def __init__(self, author):
        self.author = author

        options = [
            discord.SelectOption(label="Enabled"),
            discord.SelectOption(label="Disabled"),
        ]
        super().__init__(
            placeholder="Activity Toggle", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if color == "Enabled":
            await interaction.response.send_message(
                content=f"{tick} Enabled", ephemeral=True
            )
            await interaction.client.db["auto activity"].update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {"enabled": True}},
                upsert=True,
            )

        if color == "Disabled":
            await interaction.response.send_message(
                content=f"{no} Disabled", ephemeral=True
            )
            await interaction.client.db["auto activity"].update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {"enabled": False}},
                upsert=True,
            )


async def MessageQuotaEmbed(
    interaction: discord.Interaction, Config: dict, embed: discord.Embed
):
    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not Config:
        Config = {"Message Quota": {}}
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    IgnoredChannels = (
        ", ".join(
            f"<#{int(Channel)}>"
            for Channel in Config.get("Message Quota", {}).get("Ignored Channels") or []
        )
        or "Not Configured"
    )
    embed.description = "> This is where you can manage your server's message quota! If you wanna know more about what this does head to the [message quota page](https://docs.astrobirb.dev/Modules/quota) on the [documentation](https:/docs.astrobirb.dev)\n"
    embed.add_field(
        name="<:settings:1207368347931516928> Message Quota",
        value=f"{replytop} `Quota:` {Config.get('Message Quota', {}).get('quota', 'Not Configured')}\n{replybottom} `Ignored Channels:` {IgnoredChannels}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)",
        inline=False,
    )
    return embed
