import discord
from utils.emojis import *
from utils.format import IsSeperateBot


class PermissionsDropdown(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            placeholder="Advanced Permissions",
            options=[
                discord.SelectOption(
                    label="Manage Permissions",
                    value="Manage Permissions",
                    emoji="<:Permissions:1207365901956026368>" if IsSeperateBot() else None,
                )
            ],
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        view = ManagePermissions(interaction.user)
        if IsSeperateBot():
            view.Add.label = "Add"
            view.Remove.label = "Remove"
        await interaction.response.send_message(
            view=view, ephemeral=True
        )


class ManagePermissions(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=360)
        self.author = author

    @discord.ui.button(
        emoji="<:Add:1163095623600447558>", style=discord.ButtonStyle.gray
    )
    async def Add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer()

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
                    emoji="<:command1:1223062616872583289>",
                )
            )

        chunks = [commands[i : i + 25] for i in range(0, len(commands), 25)]
        view = PaginateViews(chunks)
        view.Previous.disabled = True
        view.add_item(Commands(self.author, commands))
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
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer()

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None or "Advanced Permissions" not in config:
            return await interaction.followup.send(
                content=f"  There are no advanced permissions set.", ephemeral=True
            )
        commands = list(config["Advanced Permissions"].keys())
        if not commands:
            return await interaction.followup.send(
                content=f"  There are no advanced permissions set.", ephemeral=True
            )

        view = discord.ui.View()
        view.add_item(RemoveCommands(self.author, commands))
        await interaction.followup.send(view=view, ephemeral=True)


class RemoveCommands(discord.ui.Select):
    def __init__(self, author: discord.Member, commands: list):
        super().__init__(
            placeholder="Select Permissions To Reset",
            min_values=0,
            max_values=len(commands),
            options=[
                discord.SelectOption(
                    label=command,
                    value=command,
                    emoji="<:command1:1223062616872583289>",
                )
                for command in commands
            ][:25],
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        await interaction.response.defer()

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})

        if config is None or "Advanced Permissions" not in config:
            return await interaction.followup.send(
                content=f"  There are no advanced permissions set.", ephemeral=True
            )
        for command in self.values:
            if command in config["Advanced Permissions"]:
                del config["Advanced Permissions"][command]
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        await interaction.edit_original_response(
            content=f"  Successfully reset advanced permissions.",
            view=None,
            embed=None,
        )


class Commands(discord.ui.Select):
    def __init__(self, author: discord.Member, commands: list[discord.SelectOption]):
        super().__init__(
            placeholder="Select Commands",
            min_values=0,
            max_values=min(len(commands), 25),
            options=commands[:25],
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        await interaction.response.defer()

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
    def __init__(self, options: list):
        super().__init__()
        self.current = 0
        self.options = options

    async def PaginateView(self, interaction: discord.Interaction):

        view = PaginateViews(self.options)
        view.current = self.current
        if self.current == 0:
            view.children[0].disabled = True
        else:
            view.children[0].disabled = False
        if self.current == len(self.options) - 1:
            view.children[1].disabled = True
        else:
            view.children[1].disabled = False

        view.add_item(Commands(interaction.user, self.options[self.current]))
        await interaction.response.edit_message(view=view, content="")

    @discord.ui.button(label="<", style=discord.ButtonStyle.gray, row=2)
    async def Previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.current == 0:
            return
        self.current -= 1
        await self.PaginateView(interaction)

    @discord.ui.button(label=">", style=discord.ButtonStyle.gray, row=2)
    async def Next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current == len(self.options) - 1:
            print(f"{self.current} == {len(self.options) - 1} k")
            return
        print(bool(self.current == len(self.options) - 1))
        self.current += 1
        await self.PaginateView(interaction)


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
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

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
        await interaction.response.edit_message(
            content=f"  Successfully updated advanced permissions.",
            view=None,
            embed=None,
        )
