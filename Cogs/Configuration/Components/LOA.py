import discord
from utils.emojis import *
from utils.HelpEmbeds import NotYourPanel


class LOAOptions(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Leave Channel",
                    emoji="<:tag:1234998802948034721>",
                    description="The channel where leaves will be sent.",
                ),
                discord.SelectOption(
                    label="Leave Audit Log",
                    emoji="<:Log:1349431938926252115>",
                    description="Logs for modify/force end.",
                ),
                discord.SelectOption(
                    label="Leave Role",
                    emoji="<:Ping:1298301862906298378>",
                    description="Gives the user a role for when they are on LOA.",
                ),
                discord.SelectOption(
                    label="Leave Mentions",
                    description="Allows for roles to be mentioned for extension & leave requests.",
                ),
            ]
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        from Cogs.Configuration.Configuration import Reset, ConfigMenu, Options

        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        await interaction.response.defer()
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {
                "LOA": {},
                "Module Options": {},
                "_id": interaction.guild.id,
            }
        await Reset(
            interaction,
            lambda: LOAOptions(interaction.user),
            lambda: ConfigMenu(Options(Config), interaction.user),
        )
        Selection = self.values[0]
        view = discord.ui.View()
        if Selection == "Leave Role":
            view.add_item(
                LOARole(
                    self.author,
                    role=interaction.guild.get_role(
                        Config.get("LOA", {}).get("role"),
                    ),
                    message=interaction.message,
                )
            )

        if Selection == "Leave Mentions":
            view.add_item(
                Mentions(
                    author=interaction.user, roles=Config.get("LOA").get("Mentions")
                )
            )

        if Selection == "Leave Channel":
            view.add_item(
                LOAChannel(
                    author=self.author,
                    channel=interaction.guild.get_channel(
                        Config.get("LOA", {}).get("channel"),
                    ),
                    message=interaction.message,
                )
            )

        if Selection == "Leave Audit Log":
            view.add_item(
                LogChannel(
                    author=self.author,
                    channel=interaction.guild.get_channel(
                        Config.get("LOA", {}).get("LogChannel"),
                    ),
                    message=interaction.message,
                )
            )

        await interaction.followup.send(view=view, ephemeral=True)


class Mentions(discord.ui.Select):
    def __init__(self, author: discord.Member, roles):
        super().__init__(
            placeholder="Leave Types",
            min_values=0,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Extension Requests",
                    description="Pings & mentions for extension requests.",
                ),
                discord.SelectOption(
                    label="Leave Requests",
                    description="Pings & mentions for leave requests.",
                ),
            ],
        )
        self.author = author
        self.roles = roles

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        Selection = self.values[0] if self.values else None
        view = discord.ui.View()

        if Selection == "Extension Requests":
            view.add_item(
                Pings(
                    author=self.author,
                    Ltype="Ext",
                    roles=[
                        role
                        for role in interaction.guild.roles
                        if role.id in self.roles.get("Ext", [])
                    ],
                )
            )

        elif Selection == "Leave Requests":
            view.add_item(
                Pings(
                    author=self.author,
                    Ltype="Leave",
                    roles=[
                        role
                        for role in interaction.guild.roles
                        if role.id in self.roles.get("Ext", [])
                    ],
                )
            )

        await interaction.response.send_message(
            content=f"<:info:1245364500874399864> **{interaction.user.display_name}**, this allows for pings to be attached to leave messages.",
            view=view,
            ephemeral=True,
        )


class Pings(discord.ui.RoleSelect):
    def __init__(
        self,
        author: discord.Member,
        roles: list[discord.Role] = None,
        message: discord.Message = None,
        Ltype: str = "Ext",
    ):
        super().__init__(
            placeholder=f"{Ltype} Pings",
            min_values=0,
            max_values=25,
            default_values=roles or [],
        )
        self.author = author
        self.roles = roles
        self.message = message
        self.Ltype = Ltype

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "LOA": {"Mentions": {}}}
        elif "LOA" not in config:
            config["LOA"] = {"Mentions": {}}
        elif "Mentions" not in config["LOA"]:
            config["LOA"]["Mentions"] = {}

        config["LOA"]["Mentions"][self.Ltype] = [role.id for role in self.values]
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.send_message(
            f"{tick} **{interaction.user.display_name}**, successfully updated mentions.",
            ephemeral=True,
        )
        try:
            await self.message.edit(
                embed=await LOAEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


class LogChannel(discord.ui.ChannelSelect):
    def __init__(
        self,
        author: discord.Member,
        channel: discord.TextChannel = None,
        message: discord.Message = None,
    ):
        super().__init__(
            placeholder="Audit Log Channel",
            min_values=0,
            max_values=1,
            default_values=[channel] if channel else [],
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author
        self.channel = channel
        self.message = message

    async def callback(self, interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "LOA": {}}
        elif "LOA" not in config:
            config["LOA"] = {}
        elif "LogChannel" not in config.get("Infraction", {}):
            config["LOA"]["LogChannel"] = None
        if self.values:
            config["LOA"]["LogChannel"] = self.values[0].id
        else:
            config["LOA"].pop("LogChannel", None)

        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await LOAEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


class LOAChannel(discord.ui.ChannelSelect):
    def __init__(
        self,
        author: discord.Member,
        channel: discord.TextChannel = None,
        message: discord.Message = None,
    ):
        super().__init__(
            min_values=0,
            max_values=1,
            default_values=[channel] if channel else [],
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author
        self.channel = channel
        self.message = message

    async def callback(self, interaction):
        from Cogs.Configuration.Configuration import ConfigMenu, Options

        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "LOA": {}}
        elif "LOA" not in config:
            config["LOA"] = {}

        config["LOA"]["channel"] = self.values[0].id if self.values else None
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await LOAEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


class LOARole(discord.ui.RoleSelect):
    def __init__(
        self,
        author: discord.Member,
        role: discord.Role = None,
        message: discord.Message = None,
    ):
        super().__init__(
            min_values=0,
            max_values=1,
            default_values=[role] if role else [],
        )
        self.author = author
        self.role = role
        self.message = message

    async def callback(self, interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "LOA": {}}
        elif "LOA" not in config:
            config["LOA"] = {}

        config["LOA"]["role"] = self.values[0].id if self.values else None
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )
        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await LOAEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


async def LOAEmbed(
    interaction: discord.Interaction, config: dict, embed: discord.Embed
):
    config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not config:
        config = {"LOA": {}}
    Channel = (
        interaction.guild.get_channel(config.get("LOA", {}).get("channel"))
        or "Not Configured"
    )
    LogChannel = (
        interaction.guild.get_channel(config.get("LOA", {}).get("LogChannel"))
        or "Not Configured"
    )

    Role = (
        interaction.guild.get_role(config.get("LOA", {}).get("role"))
        or "Not Configured"
    )
    if isinstance(Role, discord.Role):
        Role = Role.mention

    if isinstance(Channel, discord.TextChannel):
        Channel = Channel.mention
    if isinstance(LogChannel, discord.TextChannel):
        LogChannel = LogChannel.mention

    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> This is where you can manage your server's LOA settings! LOA is a way for staff members to take a break from their duties. You can find out more at [the documentation](https://docs.astrobirb.dev/Modules/loa)."
    embed.add_field(
        name="<:settings:1207368347931516928> LOA",
        value=f"{replytop} `LOA Channel:` {Channel}\n{replymiddle} `LOA Audit Channel`: {LogChannel}\n{replybottom} `LOA Role:` {Role}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev/Modules/loa)",
        inline=False,
    )
    return embed
