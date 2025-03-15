import discord
import discord.http

from utils.emojis import *

from dotenv import load_dotenv

load_dotenv()
# Mongos = AsyncIOMotorClient(os.getenv("MONGO_URL"))
# DB = Mongos["astro"]
# Configuration = DB["Config"]


async def ModuleOptions(Config, data = None):
    if not Config:
        Config = {"Modules": {}}
    return [
        discord.SelectOption(
            label="Infractions",
            description="",
            emoji="<:Infraction:1223063128275943544>",
            value="infractions",
            default=Config.get("Modules", {}).get("infractions", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Promotions",
            description="",
            emoji="<:Promotion:1234997026677198938>",
            value="promotions",
            default=Config.get("Modules", {}).get("promotions", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Message Quota",
            description="",
            value="Quota",
            emoji="<:messageQuota:1224722310687359106>",
            default=Config.get("Modules", {}).get("Quota", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Forums",
            description="",
            value="Forums",
            emoji="<:forum:1223062562782838815>",
            default=Config.get("Modules", {}).get("Forums", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Daily Questions",
            emoji="<:qotd:1234994772796772432>",
            description="",
            value="QOTD",
            default=Config.get("Modules", {}).get("QOTD", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Leave Of Absence",
            description="",
            value="LOA",
            emoji="<:LOA:1223063170856390806>",
            default=Config.get("Modules", {}).get("LOA", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Suspensions",
            description="",
            value="suspensions",
            emoji="<:suspensions:1234998406938755122>",
            default=Config.get("Modules", {}).get("suspensions", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Ban Appeal",
            description="",
            emoji="<:reports:1224723845726998651>",
            value="Ban Appeal",
            default=Config.get("Modules", {}).get("Ban Appeal", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Suggestions",
            description="",
            value="suggestions",
            emoji="<:suggestion:1207370004379607090>",
            default=Config.get("Modules", {}).get("suggestions", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Tickets",
            description="",
            value="Tickets",
            emoji="<:messagereceived:1201999712593383444>",
            default=Config.get("Modules", {}).get("Tickets", False) or False if not data else False,
        ),        
        discord.SelectOption(
            label="Modmail",
            description="",
            value="Modmail",
            emoji="<:messagereceived:1201999712593383444>",
            default=Config.get("Modules", {}).get("Modmail", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Custom Commands",
            description="",
            value="customcommands",
            emoji="<:command1:1223062616872583289>",
            default=Config.get("Modules", {}).get("customcommands", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Staff List",
            description="",
            value="Staff List",
            emoji="<:StaffList:1264584889727193159>",
            default=Config.get("Modules", {}).get("Staff List", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Staff Feedback",
            description="",
            value="Feedback",
            emoji="<:stafffeedback:1235000485208002610>",
            default=Config.get("Modules", {}).get("Feedback", False) or False if not data else False,
        ),
        discord.SelectOption(
            label="Staff Panel",
            description="",
            value="Staff Database",
            emoji="<:staffdb:1206253848298127370>",
            default=Config.get("Modules", {}).get("Staff Database", False) or False if not data else False, 
        ),
        discord.SelectOption(
            label="Auto Response",
            value="Auto Responder",
            emoji="<:autoresponse:1250481563615887391>",
            default=Config.get("Modules", {}).get("Auto Responder", False) or False if not data else False,
        ),

        discord.SelectOption(
            label="Connection Roles",
            value="connectionroles",
            emoji="<:link:1206670134064717904>",
            default=Config.get("Modules", {}).get("connectionroles", False) or False if not data else False,
        ),
    ]


class ModuleToggle(discord.ui.Select):
    def __init__(self, author, options: list):
        self.author = author
        super().__init__(
            placeholder="Modules",
            options=options,
            min_values=0,
            max_values=len(options),
        )

    async def callback(self, interaction: discord.Interaction):
        from Cogs.Configuration.Configuration import ConfigMenu
        from Cogs.Configuration.Configuration import Options

        Selected = self.values
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"_id": interaction.guild.id, "Modules": {}}
        elif "Modules" not in config:
            config["Modules"] = {}

        for module in config["Modules"]:
            config["Modules"][module] = False

        for module in Selected:
            config["Modules"][module] = True
        if "Modmail" in Selected:
            if not interaction.guild.chunked:
                await interaction.guild.chunk()
        if "promotions" in Selected:
            from Cogs.Modules.promotions import SyncServer
            try:
             await SyncServer(interaction.client, interaction.guild)
            except:
                pass

        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}, upsert=True
        )
        Updated = await interaction.client.config.find_one({"_id": interaction.guild.id})
        view = discord.ui.View()
        view.add_item(ModuleToggle(interaction.user, await ModuleOptions(Updated)))
        view.add_item(ConfigMenu(Options(Updated), interaction.user))

        await interaction.response.edit_message(view=view)
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
