import discord
import discord.http
import traceback
from utils.format import IsSeperateBot

from utils.emojis import *

from dotenv import load_dotenv
from typing import Literal

load_dotenv()


class Tickets(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Panels", emoji="<:Panel:1340741181965078642>"
                ),
                discord.SelectOption(
                    label="Multi Panels", emoji="<:MultiPanel:1340741183579885690>"
                ),
                discord.SelectOption(
                    label="Quota", emoji="<:counting:1343598685749252227>"
                ),
            ]
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        option = self.values[0]

        if option == "Panels":
            view = discord.ui.View()
            view.add_item(CreateDeletePanel(self.author, "single"))
            await interaction.response.send_message(view=view, ephemeral=True)

        elif option == "Multi Panels":
            view = discord.ui.View()
            view.add_item(CreateDeletePanel(self.author, "multi"))
            await interaction.response.send_message(view=view, ephemeral=True)
        elif option == "Quota":
            await interaction.response.send_modal(
                TicketQuota(
                    self.author,
                    await interaction.client.config.find_one(
                        {"_id": interaction.guild.id}
                    ),
                )
            )


class TicketQuota(discord.ui.Modal):
    def __init__(self, author: discord.Member, config: dict):
        super().__init__(title="Ticket Quota")
        self.author = author
        self.quota = discord.ui.TextInput(
            label="Quota",
            placeholder="Amount of claimed tickets.",
            default=config.get("Tickets", {}).get("quota", 0),
        )
        self.add_item(self.quota)

    async def on_submit(self, interaction: discord.Interaction):
        quota = self.quota.value
        Config = await interaction.client.config.find_one(
            {"guild": interaction.guild.id}
        )
        if not Config:
            Config = {
                "_id": interaction.guild.id,
                "Tickets": {"quota": 0, "TimeFrame": None},
            }

        Config["Tickets"]["quota"] = quota
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id},
            {"$set": Config},
        )
        await interaction.response.send_message(
            content=f"  **{interaction.user.display_name},** ticket quota updated successfully.",
            ephemeral=True,
        )


class CreateDeletePanel(discord.ui.Select):
    def __init__(self, author: discord.Member, PanelType: Literal["single", "multi"]):
        Options = [
            discord.SelectOption(label="Create", emoji="<:Add:1163095623600447558>"),
            discord.SelectOption(
                label="Delete", emoji="<:Subtract:1229040262161109003>"
            ),
            discord.SelectOption(label="Modify", emoji="<:Pen:1235001839036923996>"),
        ]
        self.PanelType = PanelType
        self.author = author
        super().__init__(options=Options)

    async def callback(self, interaction: discord.Interaction):
        Action = self.values[0]

        if Action == "Create":
            await interaction.response.send_modal(PanelCreationModal(self.PanelType))

        elif Action == "Delete":
            PanelsList = (
                await interaction.client.db["Panels"]
                .find({"guild": interaction.guild.id, "type": self.PanelType})
                .to_list(length=None)
            )
            Options = [
                discord.SelectOption(label=Panel.get("name", "Unnamed"))
                for Panel in PanelsList
            ]

            if not Options:
                await interaction.response.send_message(
                    content="No panels found to delete.", ephemeral=True
                )
                return

            View = discord.ui.View()
            View.add_item(DeletePanelSelect(self.author, self.PanelType, Options))
            await interaction.response.edit_message(view=View)

        elif Action == "Modify":
            PanelsList = (
                await interaction.client.db["Panels"]
                .find({"guild": interaction.guild.id, "type": self.PanelType})
                .to_list(length=None)
            )
            Options = [
                discord.SelectOption(label=Panel.get("name", "Unnamed"))
                for Panel in PanelsList
            ]

            if not Options:
                await interaction.response.send_message(
                    content="No panels found to modify.", ephemeral=True
                )
                return

            View = discord.ui.View()
            View.add_item(ModifyPanelSelect(self.author, self.PanelType, Options))
            await interaction.response.edit_message(view=View)


class ModifyPanelSelect(discord.ui.Select):
    def __init__(self, author: discord.Member, PanelType: str, options: list):
        super().__init__(options=options)
        self.author = author
        self.PanelType = PanelType

    async def callback(self, interaction: discord.Interaction):
        SelectedPanel = self.values[0]

        if self.PanelType == "single":
            View = SingelPanelCustomisation(interaction.user, SelectedPanel)
            Styler = await interaction.client.db["Panels"].find_one(
                {"guild": interaction.guild.id, "type": "single", "name": SelectedPanel}
            )
            View.Reviews.label = (
                "Allow Ratings (Enabled)"
                if Styler.get("AllowReviews", False)
                else "Allow Ratings (Disabled)"
            )
            View.Reviews.style = (
                discord.ButtonStyle.green
                if Styler.get("AllowReviews", False)
                else discord.ButtonStyle.red
            )
        else:
            View = MultiPanelCustomisation(interaction.user, SelectedPanel)

        await interaction.response.edit_message(view=View)


class PanelCreationModal(discord.ui.Modal):
    def __init__(self, PanelType: Literal["single", "multi"]):
        self.PanelType = PanelType
        super().__init__(title="Create New Panel")

        self.name_input = discord.ui.TextInput(
            label="Panel Name", placeholder="Enter a name for your new panel"
        )
        self.add_item(self.name_input)

    async def on_submit(self, interaction: discord.Interaction):
        if await interaction.client.db["Panels"].find_one(
            {
                "guild": interaction.guild.id,
                "type": self.PanelType,
                "name": self.name_input.value,
            }
        ):
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** a panel with that name already exists.",
                ephemeral=True,
            )
        PanelName = self.name_input.value
        await interaction.client.db["Panels"].insert_one(
            {"guild": interaction.guild.id, "type": self.PanelType, "name": PanelName}
        )

        if self.PanelType == "single":
            View = SingelPanelCustomisation(interaction.user, PanelName)

        else:
            View = MultiPanelCustomisation(interaction.user, PanelName)

        await interaction.response.edit_message(view=View)


class DeletePanelSelect(discord.ui.Select):
    def __init__(self, author: discord.Member, PanelType: str, options: list):
        super().__init__(options=options)
        self.author = author
        self.PanelType = PanelType

    async def callback(self, interaction: discord.Interaction):
        SelectedPanel = self.values[0]
        await interaction.client.db["Panels"].delete_one(
            {
                "guild": interaction.guild.id,
                "type": self.PanelType,
                "name": SelectedPanel,
            }
        )
        await interaction.response.edit_message(
            content=f"Panel '{SelectedPanel}' deleted successfully.",
            view=None,
            embed=None,
        )


class SingelPanelCustomisation(discord.ui.View):
    def __init__(self, author: discord.Member, name: str):
        super().__init__(timeout=3060)
        self.name = name
        self.author = author

    @discord.ui.button(
        label="Customise Embeds",
        style=discord.ButtonStyle.gray,
        emoji="<:Customisation:1223063306131210322>",
    )
    async def CustomiseEmbed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        view = discord.ui.View()
        view.add_item(EmbedSelection(interaction.user, "Panel", self.name))
        await interaction.response.send_message(view=view)

    @discord.ui.button(label="Customise Button", emoji="<:Button:1223063359184830494>")
    async def CustomiseButton(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        custom = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name}
        )
        await interaction.response.send_modal(
            CustomiseButton(interaction.user, self.name, custom)
        )

    @discord.ui.button(
        label="Category",
        style=discord.ButtonStyle.blurple,
        emoji="<:category:1248312604733210735>",
    )
    async def Category(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        custom = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name}
        )
        view = discord.ui.View()
        view.add_item(
            Category(
                interaction.user,
                self.name,
                interaction.guild.get_channel(custom.get("Category", 0)),
            )
        )
        await interaction.response.send_message(view=view, ephemeral=True)

    @discord.ui.button(
        label="Transcript Channel",
        style=discord.ButtonStyle.blurple,
        emoji="<:tag:1234998802948034721>",
    )
    async def Transcript(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        custom = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name}
        )

        view = discord.ui.View()
        view.add_item(
            TranscriptChannel(
                interaction.user,
                self.name,
                interaction.guild.get_channel(custom.get("TranscriptChannel", 0)),
            )
        )
        await interaction.response.send_message(view=view, ephemeral=True)

    @discord.ui.button(
        label="Permissions",
        style=discord.ButtonStyle.blurple,
        emoji="<:Permissions:1207365901956026368>",
    )
    async def Permissions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        custom = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name}
        )

        view = discord.ui.View()
        view.add_item(
            Permissions(
                interaction.user,
                self.name,
                [
                    role
                    for role in interaction.guild.roles
                    if role.id in custom.get("permissions", [])
                ],
            )
        )
        embed = discord.Embed(
            description="Select the roles that can manage the ticket.",
            color=discord.Color.dark_embed()
        ).set_author(name="Permissions", icon_url=interaction.guild.icon)

        await interaction.response.send_message(view=view, embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Mentions On Open",
        style=discord.ButtonStyle.blurple,
        emoji="<:Ping:1298301862906298378>",
    )
    async def Mentions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        custom = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name}
        )
        view = discord.ui.View()
        view.add_item(
            MentionsOnOpen(
                interaction.user,
                self.name,
                [
                    role
                    for role in interaction.guild.roles
                    if role.id in custom.get("MentionsOnOpen", [])
                ],
            )
        )
        await interaction.response.send_message(view=view, ephemeral=True)

    @discord.ui.button(
        label="Access Control",
        style=discord.ButtonStyle.blurple,
        emoji="<:AccessControl:1340741536492814458>",
    )
    async def AccessControl(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        custom = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name}
        )
        view = discord.ui.View()

        view.add_item(
            AccessControl(
                interaction.user,
                self.name,
                [
                    role
                    for role in interaction.guild.roles
                    if role.id in custom.get("AccessControl", [])
                ],
            )
        )
        embed = discord.Embed(
            description="Select the roles that can open tickets.",
            color=discord.Color.dark_embed()
        ).set_author(name="Access Control", icon_url=interaction.guild.icon)
        await interaction.response.send_message(view=view, embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Automations",
        style=discord.ButtonStyle.blurple,
        emoji="<:reports:1224723845726998651>",
    )
    async def Automations(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        custom = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name}
        )

        await interaction.response.send_modal(
            Automations(interaction.user, self.name, custom)
        )

    def FormEmbed(self, dict: dict):
        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(
            name=f"{dict.get('name', 'Unnamed')} Panel",
        )

        for i, question in enumerate(dict.get("Questions", [])):
            embed.add_field(
                name=f"Question {i + 1}",
                value=f"> **Label:** {question.get('label')}\n"
                f"> **Placeholder:** {question.get('placeholder') if question.get('placeholder') else 'None'}\n"
                f"> **Min Length:** {question.get('min') if question.get('min') else 'None'}\n"
                f"> **Max Length:** {question.get('max') if question.get('max') else 'None'}\n"
                f"> **Required:** {question.get('required') if question.get('required') else 'None'}\n",
            )

        if len(dict.get("Questions", [])) < 0:
            embed.description = "> You can add up to 5 questions to this form."

        return embed

    @discord.ui.button(
        label="Forms",
        style=discord.ButtonStyle.blurple,
        emoji="<:Application:1224722901328986183>",
    )
    async def Forms(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        custom = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name}
        )

        view = TicketForms(interaction.user, self.name, self.FormEmbed)
        if IsSeperateBot():
            view.DeleteQuestion.label = "Delete"
            view.AddQuestion.label = f"Add ({len(custom.get('Questions', []))}/5)"
        
        else:
            view.AddQuestion.label = f"({len(custom.get('Questions', []))}/5)"
        if len(custom.get("Questions", [])) >= 5:
            view.AddQuestion.disabled = True
        await interaction.response.send_message(
            view=view, embed=self.FormEmbed(custom), ephemeral=True
        )

    @discord.ui.button(
        label="Allow Ratings (Disabled)",
        style=discord.ButtonStyle.red,
        emoji="<:Reviews:1340741536492814458>",
    )
    async def Reviews(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        custom = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name}
        )
        if not custom:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** this panel does not exist.",
                ephemeral=True,
            )

        AllowReviews = not custom.get("AllowReviews", False)

        await interaction.client.db["Panels"].update_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name},
            {"$set": {"AllowReviews": AllowReviews}},
        )

        button.style = (
            discord.ButtonStyle.green if AllowReviews else discord.ButtonStyle.red
        )
        button.label = (
            "Allow Ratings (Enabled)" if AllowReviews else "Allow Ratings (Disabled)"
        )

        await interaction.response.edit_message(view=self)

    @discord.ui.button(
        label="Finish",
        style=discord.ButtonStyle.green,
        emoji="<:Save:1223293419678470245>",
    )
    async def Finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        custom = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name}
        )
        if not custom:
            await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** this panel does not exist.",
                ephemeral=True,
            )
            return

        Required = ["permissions", "Category", "TranscriptChannel", "Button"]
        MissingFields = []
        for field in Required:
            if not custom.get(field):
                MissingFields.append(field)

        if len(MissingFields) > 0:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** missing required fields: {', '.join(MissingFields)}",
                ephemeral=True,
            )

        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** configuration finished.",
            view=None,
        )


class Automations(discord.ui.Modal):
    def __init__(self, author: discord.Member, name: str, data: dict):
        super().__init__(title="Automations")
        self.author = author
        self.name = name
        self.Inactivity = discord.ui.TextInput(
            label="Inactivity Reminder",
            placeholder="How long before a reminder is sent? (Minutes)",
            default=data.get("Automations", {}).get("Inactivity", "120"),
        )
        self.add_item(self.Inactivity)

    async def on_submit(self, interaction: discord.Interaction):
        Inactivity = self.Inactivity.value
        Config = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name}
        )
        if not Config:
            Config = {"_id": interaction.guild.id, "Automations": {"Inactivity": "120"}}
        if not Config.get("Automations"):
            Config["Automations"] = {"Inactivity": "120"}

        if not isinstance(Inactivity, int):
            try:
                Inactivity = int(Inactivity)
            except:
                return await interaction.response.send_message(
                    content=f"  **{interaction.user.display_name},** inactivity must be an integer.",
                    ephemeral=True,
                )

        Config["Automations"]["Inactivity"] = Inactivity
        await interaction.client.db["Panels"].update_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name},
            {"$set": Config},
            upsert=True,
        )
        await interaction.response.send_message(
            content=f"  **{interaction.user.display_name},** inactivity reminder updated successfully.",
            ephemeral=True,
        )


class MultiPanelCustomisation(discord.ui.View):
    def __init__(self, author: discord.Member, name: str):
        super().__init__(timeout=3060)
        self.name = name
        self.author = author

    @discord.ui.button(
        label="Customise Embeds",
        style=discord.ButtonStyle.gray,
        emoji="<:Customisation:1223063306131210322>",
    )
    async def CustomiseEmbed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        view = discord.ui.View()
        view.add_item(EmbedSelection(interaction.user, "Multi", self.name))
        await interaction.response.send_message(view=view)

    @discord.ui.button(label="Manage Panels", emoji="<:MultiPanel:1340741183579885690>")
    async def ManagePanels(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        panels = (
            await interaction.client.db["Panels"]
            .find({"guild": interaction.guild.id, "type": "single"})
            .to_list(length=None)
        )
        panel = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "multi", "name": self.name}
        )
        Default = panel.get("Panels", [])
        options = [
            discord.SelectOption(
                label=p.get("name", "Unnamed"), default=p.get("name") in Default
            )
            for p in panels
        ]
        if not options:
            await interaction.response.send_message(
                content="No panels found.", ephemeral=True
            )
            return
        view = discord.ui.View()
        view.add_item(MultiToSingle(interaction.user, self.name, options))
        await interaction.response.send_message(view=view, ephemeral=True)

    @discord.ui.button(
        label="Finish",
        style=discord.ButtonStyle.green,
        emoji="<:Save:1223293419678470245>",
    )
    async def Finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        custom = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "multi", "name": self.name}
        )
        if not custom:
            await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** this panel does not exist.",
                ephemeral=True,
            )
            return

        Required = ["Panels"]
        MissingFields = []
        for field in Required:
            if not custom.get(field):
                MissingFields.append(field)

        if len(MissingFields) > 0:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** missing required fields: {', '.join(MissingFields)}",
                ephemeral=True,
            )

        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** configuration finished.",
            view=None,
        )


async def CustomiseEmbed(interaction: discord.Interaction, option, name):
    try:
        await interaction.response.defer()
        custom = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "name": name}
        )
        embed = None

        from Cogs.Configuration.Components.EmbedBuilder import (
            DisplayEmbed,
            Embed,
            NoEmbed,
        )

        Default = {
            "thumb": "",
            "author_url": "",
            "option": option,
            "image": "",
            "name": name,
        }

        if not custom or custom.get(option) is None:
            view = Embed(
                interaction.user,
                FinalFunction,
                option,
                Default,
            )
            embed = discord.Embed(
                title="Unknown",
            )

            view.remove_item(view.Buttons)
            if option != "Panel":
                view.remove_item(view.Content)
                view.remove_item(view.RemoveEmbed)
            view.remove_item(view.Permissions)
            view.remove_item(view.ForumsChannel)
            view.remove_item(view.Ping)
            view.remove_item(view.reset)

            return await interaction.edit_original_response(
                embed=embed, view=view, content=None
            )
        view = Embed(interaction.user, FinalFunction, option, Default)
        if custom.get(option).get("embed") is not None:
            embed = await DisplayEmbed(custom.get(option), interaction.user)

        if not embed:
            view = NoEmbed(interaction.user, FinalFunction, name, Default)

        if option != "Panel":
            view.remove_item(view.Content)
            view.remove_item(view.RemoveEmbed)
        view.remove_item(view.Buttons)
        view.remove_item(view.Permissions)
        if embed:
            view.remove_item(view.ForumsChannel)
            view.remove_item(view.Ping)
        view.remove_item(view.reset)

        return await interaction.edit_original_response(
            embed=embed, view=view, content=custom.get(option).get("content", None)
        )
    except Exception as e:
        traceback.print_exc()


async def FinalFunction(interaction: discord.Interaction, d={}):
    embed = interaction.message.embeds
    if embed and interaction.message is None:
        return await interaction.response.send_message(
            content=f"  **{interaction.user.display_name},** you can't have an empty message.",
        )
    RemoveEmbed = False
    if embed:
        embed = embed[0]
        data = {
            f"{d.get('option')}": {
                "content": interaction.message.content,
                "creator": interaction.user.id,
                "embed": {
                    "title": embed.title,
                    "description": embed.description,
                    "thumbnail": d.get("thumb"),
                    "image": d.get("image"),
                    "color": f"{embed.color.value:06x}" if embed.color else None,
                    "author": {
                        "name": embed.author.name if embed.author else None,
                        "icon_url": d.get("author_url"),
                    },
                    "fields": [
                        {
                            "name": field.name,
                            "value": field.value,
                            "inline": field.inline,
                        }
                        for field in embed.fields
                    ],
                },
            }
        }
    else:
        print(d)
        data = {
            f"{d.get('option')}": {
                "content": interaction.message.content,
                "creator": interaction.user.id,
            }
        }
        RemoveEmbed = True

    Update = {"$set": data}

    if RemoveEmbed:
        Update["$unset"] = {"embed": ""}

    await interaction.client.db["Panels"].update_one(
        {"guild": interaction.guild.id, "name": d.get("name")}, Update, upsert=True
    )
    

    await interaction.response.send_message(
        content=f"  **{interaction.user.display_name}**, succesfully updated `{d.get('option')}` embed.",
        embed=None,
        ephemeral=True
    )
    try:
        await interaction.message.delete()
    except (discord.NotFound, discord.Forbidden):
        return


class EmbedSelection(discord.ui.Select):
    def __init__(self, author: discord.Member, type: str, name: str):
        if type == "Panel":
            options = [
                discord.SelectOption(label="Panel", value="Panel"),
                discord.SelectOption(label="Welcome Message", value="Welcome Message"),
                discord.SelectOption(label="Close Request", value="Close Request"),
            ]
        else:
            options = [
                discord.SelectOption(label="Panel", value="Panel"),
            ]
        super().__init__(options=options)
        self.author = author
        self.name = name

    async def callback(self, interaction: discord.Interaction):

        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        option = self.values[0]
        await CustomiseEmbed(interaction, option, self.name)


class MultiToSingle(discord.ui.Select):
    def __init__(self, author: discord.Member, name: str, options: list):
        super().__init__(options=options[:25], max_values=len(options), min_values=0)
        self.name = name
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.client.db["Panels"].update_one(
            {"guild": interaction.guild.id, "type": "multi", "name": self.name},
            {"$set": {"Panels": self.values}},
        )
        return await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** I've succesfully updated the connected panels.",
            embed=None,
            view=None,
        )


async def TicketsEmbed(interaction: discord.Interaction, embed: discord.Embed):
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = (
        "> The Tickets Panel allows users to create and manage tickets for support, "
        "inquiries, or reports. You can customize ticket categories, forms, and permissions. "
        "Learn more at [the documentation](https://docs.astrobirb.dev/)."
    )
    return embed


class Permissions(discord.ui.RoleSelect):
    def __init__(self, author: discord.Member, name: str, permissions: list):
        super().__init__(
            placeholder="Select roles for permissions",
            min_values=1,
            max_values=25,
            default_values=permissions,
        )
        self.author = author
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        selected_roles = [role.id for role in self.values]
        await interaction.client.db["Panels"].update_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name},
            {"$set": {"permissions": selected_roles}},
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** permissions updated successfully.",
            view=None,
            embed=None
        )


class TranscriptChannel(discord.ui.ChannelSelect):
    def __init__(self, author: discord.Member, name: str, channel: discord.TextChannel):
        super().__init__(
            placeholder="Select a channel",
            min_values=1,
            max_values=1,
            default_values=[channel] if channel else [],
        )
        self.author = author
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.client.db["Panels"].update_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name},
            {"$set": {"TranscriptChannel": self.values[0].id if self.values else None}},
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** transcript channel updated successfully.",
            view=None,
        )


class TicketForms(discord.ui.View):
    def __init__(self, author: discord.Member, panel: str, embed: callable):
        super().__init__(timeout=None)
        self.author = author
        self.panel = panel
        self.embed = embed

    @discord.ui.button(
        label="(0/5)",
        style=discord.ButtonStyle.gray,
        emoji="<:Add:1163095623600447558>",
    )
    async def AddQuestion(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            Question(interaction.user, self.panel, self.embed)
        )

    @discord.ui.button(
        style=discord.ButtonStyle.gray,
        emoji="<:Subtract:1229040262161109003>",
    )
    async def DeleteQuestion(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        Config = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.panel}
        )
        if not Config:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** this panel does not exist.",
                ephemeral=True,
            )

        if len(Config.get("Questions", [])) == 0:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** there are no questions to delete.",
                ephemeral=True,
            )

        Questions = [label for label in Config.get("Questions", [])]
        view = discord.ui.View()
        view.add_item(
            DeleteQuestionSelect(interaction.user, self.panel, Questions, self.embed)
        )

        await interaction.response.edit_message(view=view)


class DeleteQuestionSelect(discord.ui.Select):
    def __init__(
        self, author: discord.Member, name: str, options: list, embed: callable
    ):
        super().__init__(
            options=[
                discord.SelectOption(label=option["label"], value=option["label"])
                for option in options
            ]
        )
        self.author = author
        self.name = name
        self.embed = embed

    async def callback(self, interaction: discord.Interaction):
        question_label = self.values[0]
        Config = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name}
        )
        if not Config:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** this panel does not exist.",
                ephemeral=True,
            )

        question = next(
            (q for q in Config.get("Questions", []) if q["label"] == question_label),
            None,
        )
        if not question:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** this question does not exist.",
                ephemeral=True,
            )

        Config["Questions"].remove(question)
        await interaction.client.db["Panels"].update_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name},
            {"$set": Config},
        )
        view = TicketForms(self.author, self.name, self.embed)
        if IsSeperateBot():
            view.DeleteQuestion.label = "Delete"
            view.AddQuestion.label = f"Add ({len(Config.get('Questions', []))}/5)"
        
        else:
            view.AddQuestion.label = f"({len(Config.get('Questions', []))}/5)"
        await interaction.response.edit_message(
            embed=self.embed(Config), content=None, view=view
        )


class Question(discord.ui.Modal):
    def __init__(self, author: discord.Member, panel: str, embed: callable):
        super().__init__(title="Add Question")
        self.author = author
        self.question = discord.ui.TextInput(
            label="Question", placeholder="Enter the question", max_length=45
        )

        self.placeholder = discord.ui.TextInput(
            label="Placeholder",
            placeholder="Enter the placeholder",
            max_length=45,
            required=False,
        )

        self.min = discord.ui.TextInput(
            label="Min Length",
            placeholder="Enter the minimum length",
            max_length=4,
            required=False,
        )
        self.max = discord.ui.TextInput(
            label="Max Length",
            placeholder="Enter the maximum length",
            max_length=4,
            required=False,
        )
        self.required = discord.ui.TextInput(
            label="Required",
            placeholder="Is this question required? (True/False)",
            max_length=5,
            required=False,
        )
        self.add_item(self.question)
        self.add_item(self.min)
        self.add_item(self.placeholder)
        self.add_item(self.max)
        self.add_item(self.required)
        self.panel = panel
        self.embed = embed

    async def on_submit(self, interaction: discord.Interaction):

        question = self.question.value
        placeholder = (
            self.placeholder.value if not self.placeholder.value == "" else None
        )
        min = self.min.value if not self.min.value == "" else None
        max = self.max.value if not self.max.value == "" else None
        required = self.required.value if not self.required.value == "" else False
        Config = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.panel}
        )
        if any(q.get("label") == question for q in Config.get("Questions", [])):
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** this question already exists.",
                ephemeral=True,
            )
        if not Config:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** this panel does not exist.",
                ephemeral=True,
            )

        if not Config.get("Questions"):
            Config["Questions"] = []

        if len(Config.get("Questions", [])) == 5:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** you can only have 5 questions.",
                ephemeral=True,
            )

        Config["Questions"].append(
            {
                "label": question,
                "placeholder": placeholder if placeholder else None,
                "min": min,
                "max": max,
                "required": required,
            }
        )
        await interaction.client.db["Panels"].update_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.panel},
            {"$set": Config},
        )
        view = TicketForms(self.author, self.panel, self.embed)
        if IsSeperateBot():
            view.DeleteQuestion.label = "Delete"
            view.AddQuestion.label = f"Add ({len(Config.get('Questions', []))}/5)"
        
        else:
            view.AddQuestion.label = f"({len(Config.get('Questions', []))}/5)"
        await interaction.response.edit_message(
            content=None, view=view, embed=self.embed(Config)
        )


class Category(discord.ui.ChannelSelect):
    def __init__(
        self, author: discord.Member, name: str, category: discord.CategoryChannel
    ):
        super().__init__(
            placeholder="Select a category",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.category],
            default_values=[category] if category else [],
        )
        self.author = author
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.client.db["Panels"].update_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name},
            {"$set": {"Category": self.values[0].id if self.values else None}},
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** category updated successfully.",
            view=None,
        )


class MentionsOnOpen(discord.ui.RoleSelect):
    def __init__(self, author: discord.Member, name: str, roles: list):
        super().__init__(
            placeholder="Select roles",
            min_values=0,
            max_values=25,
            default_values=roles,
        )
        self.author = author
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        selected_roles = [role.id for role in self.values]
        await interaction.client.db["Panels"].update_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name},
            {"$set": {"MentionsOnOpen": selected_roles}},
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** mentions on open updated successfully.",
            view=None,
        )


class AccessControl(discord.ui.RoleSelect):
    def __init__(self, author: discord.Member, name: str, roles: list):
        super().__init__(
            placeholder="Select roles",
            min_values=0,
            max_values=25,
            default_values=roles,
        )
        self.author = author
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.client.db["Panels"].update_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name},
            {"$set": {"AccessControl": [role.id for role in self.values]}},
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** access control updated successfully.",
            view=None,
            embed=None
        )


class CustomiseButton(discord.ui.Modal):
    def __init__(self, author: discord.Member, name: str, data: dict):
        super().__init__(title="Customise Button")
        self.author = author
        self.name = name
        self.button = discord.ui.TextInput(
            label="Button",
            placeholder="Enter the button name",
            default=data.get("Button", {}).get("label", ""),
        )
        self.color = discord.ui.TextInput(
            label="Color",
            placeholder="Enter the button color (Blurple, Green, Red, Grey)",
            default=data.get("Button", {}).get("style", ""),
            required=False,
        )
        self.emoji = discord.ui.TextInput(
            label="Emoji",
            placeholder="Enter the button emoji",
            default=data.get("Button", {}).get("emoji", ""),
            required=False,
        )
        self.add_item(self.button)
        self.add_item(self.color)
        self.add_item(self.emoji)

    async def on_submit(self, interaction: discord.Interaction):
        button = self.button.value
        color = self.color.value
        emoji = self.emoji.value
        if not color:
            color = "Grey"
        if not color in ["Blurple", "Green", "Red", "Grey"]:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** invalid button color.",
                ephemeral=True,
            )
        if not emoji:
            emoji = None
        import string
        import random

        await interaction.client.db["Panels"].update_one(
            {"guild": interaction.guild.id, "type": "single", "name": self.name},
            {
                "$set": {
                    "Button": {
                        "label": button,
                        "style": color,
                        "emoji": emoji,
                        "custom_id": "".join(
                            random.choices(string.ascii_letters + string.digits, k=32)
                        ),
                    }
                }
            },
        )
        await interaction.response.send_message(
            content=f"  **{interaction.user.display_name},** button updated successfully.",
            ephemeral=True,
        )
