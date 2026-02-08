import discord
import traceback
from utils.emojis import *
import re
import typing
from utils.permissions import premium
from utils.HelpEmbeds import NoPremium, Support, NotYourPanel


class HSELECT(discord.ui.Select):
    def __init__(
        self,
        author: discord.Member,
        system: typing.Literal["multi", "single", "og"] = "og",
    ):
        options = [
            discord.SelectOption(
                label="System",
                value="System",
                emoji="<:system:1341493634733703300>",
                description="Choose which system you want to use.",
            ),
        ]
        if system == "single":
            options.append(
                discord.SelectOption(
                    label="Hierarchy",
                    value="Single Hierarchy",
                    emoji="<:hierarchy:1341493421503676517>",
                )
            )
        elif system == "multi":
            options.append(
                discord.SelectOption(
                    label="Hierarchy",
                    value="Multi Hierarchy",
                    emoji="<:hierarchy:1341493421503676517>",
                )
            )

        super().__init__(options=options)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {
                "Promo": {},
                "Module Options": {},
                "_id": interaction.guild.id,
            }
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        Selected = self.values[0]
        await interaction.response.defer()
        if Selected == "System":
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            system_type = config.get("Promo", {}).get("System", {}).get("type", "og")
            view = discord.ui.View()
            view.add_item(
                ModmailSystem(
                    interaction.user,
                    [
                        discord.SelectOption(
                            label="Single Hierarchy",
                            value="single",
                            default=(system_type == "single"),
                        ),
                        discord.SelectOption(
                            label="Multi Hierarchy",
                            value="multi",
                            default=(system_type == "multi"),
                        ),
                        discord.SelectOption(
                            label="OG System", value="og", default=(system_type == "og")
                        ),
                    ],
                    interaction.message,
                )
            )
            return await interaction.followup.send(
                view=view,
                ephemeral=True,
            )
        elif Selected == "Single Hierarchy":
            view = discord.ui.View()
            hierarchy_roles = (
                Config.get("Promo", {})
                .get("System", {})
                .get("single", {})
                .get("Hierarchy", [])
            )
            roles = [
                role for role in interaction.guild.roles if role.id in hierarchy_roles
            ]
            view.add_item(SingleHierarchy(interaction.user, roles))
            return await interaction.followup.send(
                view=view,
                ephemeral=True,
                content="<:List:1223063187063308328> Select the roles for the hierarchy.\n\n<:Help:1223063068012056576> No need to select them in order, they will be sorted automatically with discords role hierarchy system.",
            )
        elif Selected == "Multi Hierarchy":
            view = discord.ui.View()
            view.add_item(CreateAndDelete(interaction.user))

            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_author(
                name="Departments",
            )
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.description = "Select **Create** to create a new department, **Delete** to delete a department, or **Modify** to modify a department."

            departments = (
                Config.get("Promo", {})
                .get("System", {})
                .get("multi", {})
                .get("Departments", [])
            )
            for department in departments:
                if (
                    isinstance(department, list)
                    and len(department) > 0
                    and isinstance(department[0], dict)
                ):
                    department = department[0]
                if isinstance(department, dict) and "ranks" in department:
                    roles = [
                        role.mention
                        for role_id in department["ranks"]
                        if (role := interaction.guild.get_role(role_id)) is not None
                    ]
                    RolesStr = "> " + ", ".join(roles) if roles else "No roles assigned"
                    if len(RolesStr) > 1024:
                        RolesStr = RolesStr[:1021] + "..."
                    embed.add_field(name=department.get("name"), value=RolesStr)
                    if len(embed.fields) >= 25:
                        break

            return await interaction.followup.send(
                view=view,
                ephemeral=True,
                embed=embed,
            )
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": Config}
        )
        await interaction.response.edit_message(view=self, content=None)


class CreateAndDelete(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            placeholder="Manage Departments",
            options=[
                discord.SelectOption(
                    label="Create", value="create", emoji="<:Add:1163095623600447558>"
                ),
                discord.SelectOption(
                    label="Delete",
                    value="delete",
                    emoji="<:Subtract:1229040262161109003>",
                ),
                discord.SelectOption(
                    label="Modify", value="modify", emoji="<:Pen:1235001839036923996>"
                ),
            ],
            min_values=1,
            max_values=1,
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        if self.values[0] == "create":
            return await interaction.response.send_modal(
                CreateDeleteDepartment(interaction.user, "create")
            )
        elif self.values[0] == "modify":
            await interaction.response.defer()

            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            if not config:
                config = {
                    "_id": interaction.guild.id,
                    "Promo": {"System": {"multi": {"Departments": []}}},
                }
            if "multi" not in config["Promo"]["System"]:
                config["Promo"]["System"]["multi"] = {"Departments": []}

            IsEmpty = (
                not config.get("Promo", {})
                .get("System", {})
                .get("multi", {})
                .get("Departments", [])
            )
            if IsEmpty:
                return await interaction.followup.send(
                    content=f"{no} **{interaction.user.display_name}**, there are no departments to modify.",
                    ephemeral=True,
                )
            view = discord.ui.View()
            view.add_item(
                ModifyDepartment(
                    interaction.user,
                    [
                        department["name"]
                        for departments_group in config["Promo"]["System"]["multi"][
                            "Departments"
                        ]
                        for department in departments_group
                    ],
                )
            )
            await interaction.edit_original_response(
                content=f"{tick} **{interaction.user.display_name}**, select the department to modify.",
                view=view,
                embed=None,
            )
            return

        elif self.values[0] == "delete":
            return await interaction.response.send_modal(
                CreateDeleteDepartment(interaction.user, "delete")
            )


class SingleHierarchy(discord.ui.RoleSelect):
    def __init__(self, author: discord.Member, roles: list[discord.Role]):
        super().__init__(
            placeholder="Select staff roles",
            min_values=1,
            max_values=25,
            default_values=roles,
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        Selected = [RoleID.id for RoleID in self.values]
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {
                "_id": interaction.guild.id,
                "Promo": {"System": {"single": {"Hierarchy": []}}},
            }

        if "single" not in config["Promo"]["System"]:
            config["Promo"]["System"]["single"] = {"Hierarchy": []}

        config["Promo"]["System"]["single"]["Hierarchy"] = Selected
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )

        await interaction.response.edit_message(
            view=None,
            content=f"{tick} **{interaction.user.display_name}**, the hierarchy has been updated!",
            embed=None,
        )


class ModmailSystem(discord.ui.Select):
    def __init__(self, author: discord.Member, options: list, msg: discord.Message):
        super().__init__(
            placeholder="System",
            options=options,
            min_values=1,
            max_values=1,
        )
        self.author = author
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        from Cogs.Configuration.Configuration import ConfigMenu, Options
        from Cogs.Modules.promotions import SyncServer

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {
                "_id": interaction.guild.id,
                "Promo": {"System": {"type": "og"}},
            }

        if "Promo" not in config:
            config["Promo"] = {"System": {"type": "og"}}
        if "System" not in config["Promo"]:
            config["Promo"]["System"] = {"type": "og"}
        if self.values:
            config["Promo"]["System"]["type"] = self.values[0]
        else:
            return await interaction.response.send_message(
                content=f"{crisis} **{interaction.user.display_name}**, no system type selected.",
                ephemeral=True,
            )
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )

        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name}**, the promotions system has been updated to {self.values[0]}!",
            view=None,
        )
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        view = discord.ui.View()
        view.add_item(
            HSELECT(
                interaction.user,
                Config.get("Promo", {}).get("System", {}).get("type", "og"),
            )
        )
        view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
        try:
            await self.msg.edit(
                embed=await HiEmbed(
                    interaction, Config, discord.Embed(color=discord.Color.dark_embed())
                ),
                view=view,
            )
        except discord.Forbidden:
            await interaction.followup.send(
                content=f"{crisis} **{interaction.user.display_name}**, I couldn't update the message. You will need to reload the page to see the new options.",
            )
        await SyncServer(interaction.client, interaction.guild)


class ModifyDepartment(discord.ui.Select):
    def __init__(self, author: discord.Member, departments: list):
        options = [
            discord.SelectOption(label=department, value=department)
            for department in departments
        ]
        super().__init__(
            placeholder="Select a department to modify",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        selected_department = self.values[0]

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {
                "_id": interaction.guild.id,
                "Promo": {"System": {"multi": {"Departments": []}}},
            }
        if "multi" not in config["Promo"]["System"]:
            config["Promo"]["System"]["multi"] = {"Departments": []}

        department = next(
            (
                d
                for group in config["Promo"]["System"]["multi"]["Departments"]
                for d in group
                if d["name"] == selected_department
            ),
            None,
        )

        if not department:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** department not found!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        roles = [
            interaction.guild.get_role(role_id)
            for role_id in department.get("ranks", [])
            if interaction.guild.get_role(role_id) is not None
        ]

        view = discord.ui.View()
        view.add_item(MultiHierarchy(interaction.user, selected_department, roles))
        await interaction.response.edit_message(
            content=f"<:List:1223063187063308328> Select the roles for the department `{selected_department}`.\n\n<:Help:1223063068012056576> No need to select them in order, they will be sorted automatically with discords role hierarchy system.",
            embed=None,
            view=view,
        )


class MultiHierarchy(discord.ui.RoleSelect):
    def __init__(
        self, author: discord.Member, department: str, roles: list[discord.Role]
    ):
        super().__init__(
            placeholder="Select department roles",
            min_values=1,
            max_values=25,
            default_values=roles,
        )
        self.author = author
        self.department = department

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        Selected = [role.id for role in self.values]
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {
                "_id": interaction.guild.id,
                "Promo": {"System": {"multi": {"Departments": []}}},
            }
        if "multi" not in config["Promo"]["System"]:
            config["Promo"]["System"]["multi"] = {
                "Departments": [{"name": self.department, "ranks": []}]
            }

        for departments_group in config["Promo"]["System"]["multi"]["Departments"]:
            for department in departments_group:
                if department["name"] == self.department:
                    department["ranks"] = Selected
                    break

        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        await interaction.response.edit_message(
            view=None,
            content=f"{tick} **{interaction.user.display_name}**, the hierarchy for the department `{self.department}` has been updated!",
            embed=None,
        )


class CreateDeleteDepartment(discord.ui.Modal):
    def __init__(self, author: discord.Member, action: str):
        super().__init__(title="Create/Delete Department", timeout=None)
        self.author = author
        self.action = action

        self.name = discord.ui.TextInput(
            label="Department Name",
            placeholder="Enter the department name",
            required=True,
        )
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {
                "_id": interaction.guild.id,
                "Promo": {"System": {"multi": {"Departments": []}}},
            }

        if "multi" not in config["Promo"]["System"]:
            config["Promo"]["System"]["multi"] = {"Departments": []}

        DepartmentName = self.name.value
        if self.action == "create":
            if any(
                department["name"] == DepartmentName
                for departments_group in config["Promo"]["System"]["multi"][
                    "Departments"
                ]
                for department in departments_group
            ):
                return await interaction.response.send_message(
                    f"{no} **{interaction.user.display_name},** I couldn't find the department.",
                    ephemeral=True,
                )

            config["Promo"]["System"]["multi"]["Departments"].append(
                [{"name": DepartmentName, "ranks": []}]
            )

            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$set": config}
            )

            view = discord.ui.View()
            view.add_item(MultiHierarchy(interaction.user, DepartmentName, []))
            await interaction.response.edit_message(
                content="<:List:1223063187063308328> Select the roles for this department's hierarchy.\n\n<:Help:1223063068012056576> No need to select them in order, they will be sorted automatically with discords role hierarchy system.",
                view=view,
            )
            return

        elif self.action == "delete":
            config["Promo"]["System"]["multi"]["Departments"] = [
                [
                    department
                    for department in departments_group
                    if department["name"] != DepartmentName
                ]
                for departments_group in config["Promo"]["System"]["multi"][
                    "Departments"
                ]
            ]

            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$set": config}
            )

            await interaction.response.edit_message(
                content=f"{tick} **{interaction.user.display_name}**, the department `{DepartmentName}` has been deleted!",
                view=None,
            )


async def HiEmbed(interaction: discord.Interaction, Config: dict, embed: discord.Embed):
    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not Config:
        Config = {"Promo": {}, "_id": interaction.guild.id}
    Promo = Config.get("Promo", {})
    System = Promo.get("System", {}).get("type", "Default")
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> This is where you can manage your server's Hierarchy settings! Hierarchy are a way to automate your role updates. You can find out more at [the documentation](https://docs.astrobirb.dev/Modules/hierarchy)."
    embed.add_field(
        name="<:settings:1207368347931516928> Hierarchy",
        value=f"> `System:` {System}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev/Modules/hierarchy).",
        inline=False,
    )

    embed.add_field(
        inline=False,
        name="<:Promotion:1234997026677198938> Promotions",
        value="> `OG System:` Members get only the role you pick. Simple one-time role assignment.\n> `Single Hierarchy:` Members move up one role at a time when promoted. They follow a ranked ladder (like level 1 → level 2 → level 3).\n> `Multiple Hierarchies:` Like Single, but you can create separate departments. Each department has its own role ladder (e.g., Moderators ladder, Support ladder).",
    )
    embed.add_field(
        inline=False,
        name="<:Infraction:1223063128275943544> Infractions",
        value=f"> `✨` **Infractions is locked behind Premium**, if you want to use this feature [join here](https://patreon.com/AstroBirb).\n\n> `OG System:` This will basically disable this system entirely, there's nothing tied to it.\n> `Single Hierarchy:` Members move down one role at a time when given infractions. They follow a ranked ladder in reverse (like level 3 → level 2 → level 1).\n> `Multiple Hierarchies:` Like Single, but you can create separate departments. Each department has its own role ladder that members move down through (e.g., Moderators ladder, Support ladder).\n> `🔔` **To allow this feature to work** you will need to edit a infraction type, and enable `Use Hierarchy`",
    )
    return embed
