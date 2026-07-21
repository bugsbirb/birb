from discord.ext import commands

from core.bot.HelpEmbeds import NotYourPanel
from core.bot.emojis import *


class Data(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_group()
    async def data(self, ctx):
        pass

    @data.command(description="Manage your server's data")
    @commands.has_guild_permissions(administrator=True)
    async def manage(self, ctx: commands.Context):
        from cogs.Configuration.Components.Modules import ModuleOptions
        from cogs.Configuration.Configuration import DefaultEmbed

        Configuration = await self.client.config.find_one({"_id": ctx.guild.id})
        if not Configuration:
            return await ctx.send(
                f"{Emojis.no} **{ctx.author.display_name}**, the config is not setup please run `/config`."
            )

        options = await ModuleOptions(Config=Configuration, data=True)
        options.extend(
            [
                discord.SelectOption(
                    label="Permissions",
                    description="Manage your server's permissions.",
                    emoji=f"{Emojis.settings_page}",
                )
            ]
        )
        for option in options:
            if option.value in ["Staff List"]:
                options.remove(option)
                break

        view = discord.ui.View()
        view.add_item(DataManage(ctx.author, options))
        embed = DefaultEmbed(ctx.guild)
        embed.title = "Data Management"
        embed.description = (
            f"{Emojis.options} Select **an option** to manage your server's data."
        )
        await ctx.send(view=view, embed=embed)

    @manage.error
    async def PermsHandler(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                f"{Emojis.no} **{ctx.author.display_name},** you are missing the `Administrator` permission."
            )


class DataManage(discord.ui.Select):
    def __init__(self, author: discord.User, options: list):
        super().__init__(options=options)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        from cogs.Configuration.Components.Infractions import InfractionEmbed
        from cogs.Configuration.Components.Promotions import PromotionEmbed
        from cogs.Configuration.Components.LOA import LOAEmbed
        from cogs.Configuration.Components.Forums import ForumsEmbed
        from cogs.Configuration.Components.Modmail import ModmailEmbed
        from cogs.Configuration.Components.Permissions import PermissionsEmbed
        from cogs.Configuration.Components.MessageQuota import MessageQuotaEmbed
        from cogs.Configuration.Components.CustomCommands import CustomCommandsEmbed
        from cogs.Configuration.Components.StaffFeedback import StaffFeedbackEmbed
        from cogs.Configuration.Components.QOTD import QOTDEMbed
        from cogs.Configuration.Components.StaffPanel import StaffPanelEmbed
        from cogs.Configuration.Components.Suggestions import SuggestionsEmbed
        from cogs.Configuration.Components.Suspensions import SuspensionEmbed
        from cogs.Configuration.Components.AutoResponse import AutoResponseEmbed

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        embed = discord.Embed(color=discord.Color.dark_embed())
        selection = self.values[0]
        view = ClearData(interaction.user, selection)
        view.remove_item(view.clear_suggestions)
        view.remove_item(view.clear_infractions)
        view.remove_item(view.clear_loa)
        view.remove_item(view.clear_promotions)
        view.remove_item(view.clear_custom_commands)
        view.remove_item(view.clear_loa)
        view.remove_item(view.clear_forums)
        view.remove_item(view.clear_staffdb)
        view.remove_item(view.clear_feedback)
        view.remove_item(view.clear_responders)
        view.remove_item(view.clear_suspensions)
        view.remove_item(view.clear_connectionroles)
        if selection == "infractions":
            embed = await InfractionEmbed(interaction, config, embed)
            view.add_item(view.clear_infractions)
        elif selection == "promotions":
            embed = await PromotionEmbed(interaction, config, embed)
            view.add_item(view.clear_promotions)

        elif selection == "LOA":
            embed = await LOAEmbed(interaction, config, embed)
            view.add_item(view.clear_loa)
            view.remove_item(view.callback)
        elif selection == "QOTD":
            embed = await QOTDEMbed(interaction, embed)

        elif selection == "Forums":
            embed = await ForumsEmbed(interaction, embed)
            view.add_item(view.clear_forums)
            view.remove_item(view.callback)
        elif selection == "Modmail":
            embed = await ModmailEmbed(interaction, config, embed)
        elif selection == "Permissions":
            embed = await PermissionsEmbed(interaction, config, embed)
        elif selection == "Quota":
            embed = await MessageQuotaEmbed(interaction, config, embed)
        elif selection == "customcommands":
            embed = await CustomCommandsEmbed(interaction, embed)
            view.add_item(view.clear_custom_commands)
        elif selection == "Feedback":
            embed = await StaffFeedbackEmbed(interaction, config, embed)
            view.add_item(view.clear_feedback)
        elif selection == "QOTD":
            embed = await QOTDEMbed(interaction, embed)
        elif selection == "Staff Database":
            embed = await StaffPanelEmbed(interaction, embed)
            view.add_item(view.clear_staffdb)
        elif selection == "suggestions":
            embed = await SuggestionsEmbed(interaction, config, embed)
            view.add_item(view.clear_suggestions)
        elif selection == "suspensions":
            embed = await SuspensionEmbed(interaction, config, embed)
            view.add_item(view.clear_suspensions)

        elif selection == "Auto Responder":
            embed = await AutoResponseEmbed(interaction, embed)
            view.remove_item(view.callback)
            view.add_item(view.clear_responders)
        elif selection == "connectionroles":
            embed = None
            view.add_item(view.clear_connectionroles)
            view.remove_item(view.callback)
        view.add_item(DataManage(interaction.user, self.options))
        await interaction.response.edit_message(embed=embed, view=view)


class ClearData(discord.ui.View):
    def __init__(self, author: discord.User, Type: str):
        super().__init__(timeout=360)
        self.author = author
        self.Type = Type

    @discord.ui.button(label="Reset Configuration", style=discord.ButtonStyle.danger)
    async def callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        from cogs.Configuration.Components.Infractions import InfractionEmbed
        from cogs.Configuration.Components.Promotions import PromotionEmbed
        from cogs.Configuration.Components.LOA import LOAEmbed
        from cogs.Configuration.Components.Modmail import ModmailEmbed
        from cogs.Configuration.Components.Permissions import PermissionsEmbed
        from cogs.Configuration.Components.MessageQuota import MessageQuotaEmbed
        from cogs.Configuration.Components.CustomCommands import CustomCommandsEmbed
        from cogs.Configuration.Components.StaffFeedback import StaffFeedbackEmbed
        from cogs.Configuration.Components.QOTD import QOTDEMbed
        from cogs.Configuration.Components.StaffPanel import StaffPanelEmbed
        from cogs.Configuration.Components.Suggestions import SuggestionsEmbed
        from cogs.Configuration.Components.Suspensions import SuspensionEmbed

        Embed = discord.Embed(color=discord.Color.dark_embed())
        if self.Type == "suspensions":
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$unset": {"Suspension": 1}}
            )
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            embed = await SuspensionEmbed(interaction, config, Embed)
        elif self.Type == "infractions":
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$unset": {"Infraction": 1}}
            )
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            embed = await InfractionEmbed(interaction, config, Embed)

        elif self.Type == "promotions":
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$unset": {"Promotions": 1}}
            )
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            embed = await PromotionEmbed(interaction, config, Embed)

        elif self.Type == "loa":
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$unset": {"LOA": 1}}
            )
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            embed = await LOAEmbed(interaction, config, Embed)

        elif self.Type == "Modmail":
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$unset": {"Modmail": 1}}
            )
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            embed = await ModmailEmbed(interaction, config, Embed)
        elif self.Type == "Permissions":
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$unset": {"Permissions": 1}}
            )
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            embed = await PermissionsEmbed(interaction, config, Embed)
        elif self.Type == "Quota":
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$unset": {"Message Quota": 1}}
            )
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            embed = await MessageQuotaEmbed(interaction, config, Embed)

        elif self.Type == "customcommands":
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$unset": {"Custom Commands": 1}}
            )
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            embed = await CustomCommandsEmbed(interaction, Embed)

        elif self.Type == "feedback":
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$unset": {"Feedback": 1}}
            )
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            embed = await StaffFeedbackEmbed(interaction, config, Embed)

        elif self.Type == "qotd":
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$unset": {"QOTD": 1}}
            )
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            embed = await QOTDEMbed(interaction, Embed)

        elif self.Type == "staffdb":
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$unset": {"Staff Database": 1}}
            )
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            embed = await StaffPanelEmbed(interaction, Embed)

        elif self.Type == "suggestions":
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$unset": {"Suggestions": 1}}
            )
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            embed = await SuggestionsEmbed(interaction, config, Embed)

        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Erase Infractions", style=discord.ButtonStyle.danger)
    async def clear_infractions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.client.db["infractions"].delete_many(
            {"guild_id": interaction.guild.id}
        )
        await interaction.response.send_message(
            f"{Emojis.tick} Successfully cleared all infractions.", ephemeral=True
        )

    @discord.ui.button(label="Erase Promotions", style=discord.ButtonStyle.danger)
    async def clear_promotions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.client.db["promotions"].delete_many(
            {"guild_id": interaction.guild.id}
        )
        await interaction.response.send_message(
            f"{Emojis.tick} Successfully cleared all promotions.", ephemeral=True
        )

    @discord.ui.button(label="Erase Suggestions", style=discord.ButtonStyle.danger)
    async def clear_suggestions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.client.db["suggestions"].delete_many(
            {"guild_id": interaction.guild.id}
        )
        await interaction.response.send_message(
            f"{Emojis.tick} Successfully cleared all suggestions.", ephemeral=True
        )

    @discord.ui.button(label="Erase Custom Commands", style=discord.ButtonStyle.danger)
    async def clear_custom_commands(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.client.db["Custom Commands"].delete_many(
            {"guild_id": interaction.guild.id}
        )
        await interaction.response.send_message(
            f"{Emojis.tick} Successfully cleared all custom commands.", ephemeral=True
        )

    @discord.ui.button(label="Erase LOA", style=discord.ButtonStyle.danger)
    async def clear_loa(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.client.db["loa"].delete_many(
            {"guild_id": interaction.guild.id}
        )
        await interaction.response.send_message(
            f"{Emojis.tick} Successfully cleared all LOA.", ephemeral=True
        )

    @discord.ui.button(
        label="Erase Forums (Configuration)", style=discord.ButtonStyle.danger
    )
    async def clear_forums(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.client.db["Forum Configuration"].delete_many(
            {"guild_id": interaction.guild.id}
        )
        await interaction.response.send_message(
            f"{Emojis.tick} Successfully cleared all forum configurations.",
            ephemeral=True,
        )

    @discord.ui.button(label="Erase Staff Database", style=discord.ButtonStyle.danger)
    async def clear_staffdb(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.client.db["staff database"].delete_many(
            {"guild_id": interaction.guild.id}
        )
        await interaction.response.send_message(
            f"{Emojis.tick} Successfully cleared all staff database.", ephemeral=True
        )

    @discord.ui.button(label="Erase Feedback", style=discord.ButtonStyle.danger)
    async def clear_feedback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.client.db["feedback"].delete_many(
            {"guild_id": interaction.guild.id}
        )
        await interaction.response.send_message(
            f"{Emojis.tick} Successfully cleared all feedback.", ephemeral=True
        )

    @discord.ui.button(label="Erase Responders", style=discord.ButtonStyle.danger)
    async def clear_responders(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.client.db["Auto Responders"].delete_many(
            {"guild_id": interaction.guild.id}
        )
        await interaction.response.send_message(
            f"{Emojis.tick} Successfully cleared all responders.", ephemeral=True
        )

    @discord.ui.button(label="Erase Suspensions", style=discord.ButtonStyle.danger)
    async def clear_suspensions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.client.db["Suspensions"].delete_many(
            {"guild_id": interaction.guild.id}
        )
        await interaction.response.send_message(
            f"{Emojis.tick} Successfully cleared all suspensions.", ephemeral=True
        )

    @discord.ui.button(label="Erase Connection Roles", style=discord.ButtonStyle.danger)
    async def clear_connectionroles(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.client.db["connectionroles"].delete_many(
            {"guild_id": interaction.guild.id}
        )
        await interaction.response.send_message(
            f"{Emojis.tick} Successfully cleared all connection roles.", ephemeral=True
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Data(client))
