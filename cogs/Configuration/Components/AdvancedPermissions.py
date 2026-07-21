from core.bot.HelpEmbeds import NotYourPanel
from core.bot.emojis import *
from core.bot.ui import BasicPaginator
from core.format import IsSeperateBot


class PermissionsDropdown(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            placeholder="Advanced Permissions",
            options=[
                discord.SelectOption(
                    label="Manage Permissions",
                    value="Manage Permissions",
                    emoji=f"{Emojis.permissions}",
                )
            ],
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        Config = await interaction.client.db["Config"].find_one(
            {"_id": interaction.guild.id}
        )

        def Embed():
            embed = discord.Embed()
            embed.set_author(
                name="Advanced Permissions",
                icon_url="https://cdn.discordapp.com/emojis/1207365901956026368.webp?size=96",
            )
            embed.set_thumbnail(url=interaction.client.user.display_avatar)
            return embed

        embed = Embed()
        embeds = []
        manage = ManagePermissions(interaction.user)  # Here bc disable button

        if (
            Config
            and Config.get("Advanced Permissions")
            and len(Config.get("Advanced Permissions")) > 0
        ):

            for i, (Perm, Roles) in enumerate(
                Config.get("Advanced Permissions").items()
            ):
                Roles = [f"<@&{r}>" for r in Roles]
                embed.add_field(
                    name=f"`{Perm}`", value=", ".join(Roles) or "None", inline=False
                )
                if (i + 1) % 5 == 0:
                    embeds.append(embed)
                    embed = Embed()
        else:
            embed.description = "-# No advanced permissions, manage them below."
            manage.Remove.disabled = True

        embeds.append(embed)

        view = BasicPaginator(author=interaction.user, embeds=embeds)

        if IsSeperateBot():
            manage.Add.label = "Add"
            manage.Remove.label = "Remove"

        for item in manage.children:
            view.add_item(item)

        await interaction.followup.send(embed=embeds[0], view=view, ephemeral=True)


class ManagePermissions(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=360)
        self.author = author

    @discord.ui.button(emoji=f"{Emojis.add}", style=discord.ButtonStyle.gray)
    async def Add(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:

            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)

        InvalidCommands = [
            "botinfo",
            "server",
            "sync",
            "tickets",
            "tickets claim",
            "config",
            "info",
            "custom",
            "custom branding",
            "quota",
            "help",
            "invite",
            "mass",
            "command",
            "command run",
            "infraction",
            "modmail",
            "support",
            "docs",
            "consent",
            "ping",
            "uptime",
            "stats",
            "github",
            "vote",
            "suggest",
            "loa",
            "staff",
            "feedback",
            "premium",
            "donate",
            "avatar",
            "user",
            "birb",
            "suspension",
            "connectionrole",
            "feedback give",
            "feedback ratings",
            "tickets closerequest",
            "tickets automation",
            "tickets close",
            "tickets blacklist",
            "tickets unblacklist",
            "tickets rename",
            "tickets remove",
            "tickets unclaim",
            "tickets add",
            "intergrations",
            "intergrations link",
            "group",
            "group membership",
            "group requests",
            "data",
        ]
        commands = []
        for command in interaction.client.cached_commands:
            if command in InvalidCommands:
                continue
            commands.append(
                discord.SelectOption(
                    label=command,
                    value=command,
                    emoji=f"{Emojis.command}",
                )
            )
        view = PaginateViews(Commands, self.author, commands)
        view.Previous.disabled = True
        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(
            name="Select the commands you want to add permissions to.",
            icon_url=interaction.guild.icon,
        )
        await interaction.edit_original_response(view=view, embed=embed)

    @discord.ui.button(
        emoji="<:Subtract:1229040262161109003>", style=discord.ButtonStyle.gray
    )
    async def Remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None or "Advanced Permissions" not in config:
            return await interaction.followup.send(
                content=f"{Emojis.no} **{interaction.user.display_name},** there are no advanced permissions set.",
                ephemeral=True,
            )
        commands = list(config["Advanced Permissions"].keys())
        if not commands:
            return await interaction.followup.send(
                content=f"{Emojis.no} **{interaction.user.display_name},** there are no advanced permissions set.",
                ephemeral=True,
            )
        view = PaginateViews(RemoveCommands, self.author, commands)
        await interaction.edit_original_response(view=view, embed=None)


class RemoveCommands(discord.ui.Select):
    def __init__(self, author: discord.Member, commands: list):
        super().__init__(
            min_values=0,
            required=False,
            max_values=len(commands),
            options=[
                discord.SelectOption(
                    label=command,
                    value=command,
                    emoji=f"{Emojis.command}",
                )
                for command in commands
            ][:25],
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})

        if config is None or "Advanced Permissions" not in config:
            return await interaction.followup.send(
                content=f"{Emojis.no} **{interaction.user.display_name}**, there are no advanced permissions set.",
                ephemeral=True,
            )
        for command in self.values:
            if command in config["Advanced Permissions"]:
                del config["Advanced Permissions"][command]
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        await interaction.edit_original_response(
            content=f"{Emojis.tick} **{interaction.user.display_name},** I've successfully reset advanced permissions.",
            view=None,
            embed=None,
        )


class Commands(discord.ui.Select):
    def __init__(self, author: discord.Member, commands: list[discord.SelectOption]):
        super().__init__(
            placeholder="Select Commands",
            min_values=0,
            required=False,
            max_values=min(len(commands), 25),
            options=commands[:25],
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "Advanced Permissions": {}}
        elif "Advanced Permissions" not in config:
            config["Advanced Permissions"] = {}

        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(
            name="Which ranks do you want to be able to access these commands?",
            icon_url=interaction.guild.icon,
        )
        view = Roles(self.author, interaction, self.values)
        await interaction.edit_original_response(embed=embed, view=view)


class PaginateViews(discord.ui.View):
    def __init__(
        self,
        Clas: type[discord.ui.Select],
        author: discord.Member,
        Options: list,
        *Args,
    ):
        super().__init__()
        self.current = 0
        self.author = author
        self.Class = Clas
        self.Args = Args
        self.chunks = [Options[i : i + 25] for i in range(0, len(Options), 25)]

        self.add_item(self.Class(self.author, *self.Args, self.chunks[self.current]))

    async def update_view(self, interaction: discord.Interaction):
        self.clear_items()
        self.add_item(self.Class(self.author, *self.Args, self.chunks[self.current]))

        self.Previous.disabled = self.current == 0
        self.Next.disabled = self.current == len(self.chunks) - 1

        self.add_item(self.Previous)
        self.add_item(self.Next)

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="<", style=discord.ButtonStyle.gray, row=2)
    async def Previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id or self.current == 0:
            return
        self.current -= 1
        await self.update_view(interaction)

    @discord.ui.button(label=">", style=discord.ButtonStyle.gray, row=2)
    async def Next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (
            interaction.user.id != self.author.id
            or self.current >= len(self.chunks) - 1
        ):
            return
        self.current += 1
        await self.update_view(interaction)


class Roles(discord.ui.View):
    def __init__(
        self, author: discord.Member, interaction: discord.Interaction, commands: list
    ):
        super().__init__()
        self.author = author
        self.interaction = interaction
        self.commands = commands
        self.add_item(RoleSelect(self.author, self.interaction, self.commands))


class RoleSelect(discord.ui.RoleSelect):
    def __init__(
        self, author: discord.Member, interaction: discord.Interaction, commands: list
    ):
        super().__init__(placeholder="Select Roles", min_values=0, max_values=25)
        self.author = author
        self.interaction = interaction
        self.commands = commands

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})

        if config is None:
            config = {"_id": interaction.guild.id, "Advanced Permissions": {}}
        elif "Advanced Permissions" not in config:
            config["Advanced Permissions"] = {}

        for command in self.commands:
            if command not in config["Advanced Permissions"]:
                config["Advanced Permissions"][command] = []
            config["Advanced Permissions"][command].extend(
                [role.id for role in self.values]
            )

        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        await interaction.edit_original_response(
            content=f"{Emojis.tick} **{interaction.user.display_name},** I've successfully updated advanced permissions.",
            view=None,
            embed=None,
        )
