import discord

from core.bot.HelpEmbeds import NotYourPanel
from core.bot.emojis import Emojis


async def ModuleOptions(Config, data=None):
    if not Config:
        Config = {"Modules": {}}
    return [
        discord.SelectOption(
            label="Infractions",
            description="",
            emoji=f"{Emojis.infractions}",
            value="infractions",
            default=(
                Config.get("Modules", {}).get("infractions", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Promotions",
            description="",
            emoji=f"{Emojis.promotions}",
            value="promotions",
            default=(
                Config.get("Modules", {}).get("promotions", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Message Quota",
            description="",
            value="Quota",
            emoji=f"{Emojis.message_quota}",
            default=(
                Config.get("Modules", {}).get("Quota", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Forums",
            description="",
            value="Forums",
            emoji=f"{Emojis.forum}",
            default=(
                Config.get("Modules", {}).get("Forums", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Daily Questions",
            emoji=f"{Emojis.qotd}",
            description="",
            value="QOTD",
            default=(
                Config.get("Modules", {}).get("QOTD", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Leave Of Absence",
            description="",
            value="LOA",
            emoji=f"{Emojis.loa}",
            default=(
                Config.get("Modules", {}).get("LOA", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Suspensions",
            description="",
            value="suspensions",
            emoji=f"{Emojis.suspensions}",
            default=(
                Config.get("Modules", {}).get("suspensions", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Suggestions",
            description="",
            value="suggestions",
            emoji=f"{Emojis.suggestion}",
            default=(
                Config.get("Modules", {}).get("suggestions", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Tickets",
            description="",
            value="Tickets",
            emoji=f"{Emojis.message_received}",
            default=(
                Config.get("Modules", {}).get("Tickets", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Modmail",
            description="",
            value="Modmail",
            emoji=f"{Emojis.message_received}",
            default=(
                Config.get("Modules", {}).get("Modmail", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Custom Commands",
            description="",
            value="customcommands",
            emoji=f"{Emojis.command}",
            default=(
                Config.get("Modules", {}).get("customcommands", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Staff List",
            description="",
            value="Staff List",
            emoji=f"{Emojis.staff_list}",
            default=(
                Config.get("Modules", {}).get("Staff List", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Staff Feedback",
            description="",
            value="Feedback",
            emoji=f"{Emojis.staff_feedback}",
            default=(
                Config.get("Modules", {}).get("Feedback", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Staff Panel",
            description="",
            value="Staff Database",
            emoji=f"{Emojis.staff_db}",
            default=(
                Config.get("Modules", {}).get("Staff Database", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Auto Response",
            value="Auto Responder",
            emoji=f"{Emojis.auto_response}",
            default=(
                Config.get("Modules", {}).get("Auto Responder", False) or False
                if not data
                else False
            ),
        ),
        discord.SelectOption(
            label="Connection Roles",
            value="connectionroles",
            emoji=f"{Emojis.link}",
            default=(
                Config.get("Modules", {}).get("connectionroles", False) or False
                if not data
                else False
            ),
        ),
    ]


class ModuleToggle(discord.ui.Select):
    def __init__(self, author, options: list):
        self.author = author
        super().__init__(
            placeholder="Modules",
            options=options,
            min_values=0,
            required=False,
            max_values=len(options),
        )

    async def callback(self, interaction: discord.Interaction):
        from cogs.Configuration.Configuration import ConfigMenu
        from cogs.Configuration.Configuration import Options

        Selected = self.values
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"_id": interaction.guild.id, "Modules": {}}
        elif "Modules" not in config:
            config["Modules"] = {}

        for module in config["Modules"]:
            config["Modules"][module] = False

        for module in Selected:
            config["Modules"][module] = True

        if "Modmail" in Selected and not interaction.guild.chunked:
            await interaction.guild.chunk()

        if "promotions" in Selected:
            from cogs.Modules.promotions import SyncServer

            try:
                await SyncServer(interaction.client, interaction.guild)
            except:
                pass

        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}, upsert=True
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )

        view = discord.ui.View()
        view.add_item(ModuleToggle(interaction.user, await ModuleOptions(Updated)))
        view.add_item(ConfigMenu(Options(Updated), interaction.user))

        await interaction.edit_original_response(view=view)
        await interaction.followup.send(
            embed=discord.Embed(
                description="-# Select **Config Menu** and set up that module!",
                color=discord.Color.brand_green(),
            ).set_author(
                name="Modules Saved",
                icon_url="https://cdn.discordapp.com/emojis/1296530049381568522.webp?size=96&quality=lossless",
            ),
            ephemeral=True,
        )
