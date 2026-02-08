import discord
import traceback
from utils.emojis import *
import re
import typing
from utils.permissions import premium
from utils.HelpEmbeds import NoPremium, Support, NotYourPanel


class PSelect(discord.ui.Select):
    def __init__(
        self,
        author: discord.Member,
    ):
        options = [
            discord.SelectOption(
                label="Promotion Channel",
                value="Promotion Channel",
                emoji="<:tag:1234998802948034721>",
                description="Set the channel for promotion messages.",
            ),
            discord.SelectOption(
                label="Promotions System",
                value="Promotions System",
                emoji="<:system:1341493634733703300>",
                description="Choose which promotions system you want to use.",
            ),
            discord.SelectOption(
                label="Webhook",
                value="Webhook",
                emoji="<:Webhook:1400197752339824821>",
                description="Send promotion messages as a webhook.",
            ),
            discord.SelectOption(
                label="Cooldown",
                value="Cooldown",
                emoji="<:Cooldown:1400468324671819786>",
                description="Set a cooldown for promoting users.",
            ),
            discord.SelectOption(
                label="Promotion Audit Log",
                value="Promotion Audit Log",
                emoji="<:Log:1349431938926252115>",
                description="Logs for creation, void, and modification.",
            ),
            discord.SelectOption(
                label="Customise Embed",
                value="Customise Embed",
                emoji="<:Customisation:1223063306131210322>",
            ),
            discord.SelectOption(
                label="Preferences",
                value="Preferences",
                emoji="<:leaf:1160541147320553562>",
                description="Set preferences for promotion behaviour.",
            ),
        ]

        super().__init__(options=options)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        from Cogs.Configuration.Configuration import ConfigMenu, Options, Reset

        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        Selected = self.values[0]

        if Selected == "Cooldown":
            await interaction.response.send_modal(
                CoolDown(author=interaction.user, message=interaction.message)
            )
            return
        await interaction.response.defer()
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {
                "Promo": {},
                "Module Options": {},
                "_id": interaction.guild.id,
            }
            
        await Reset(
            interaction,
            lambda: PSelect(interaction.user),
            lambda: ConfigMenu(Options(Config), interaction.user),
        )
        if Selected == "Promotion Channel":
            view = discord.ui.View()
            view.add_item(
                PromotionChannel(
                    interaction.user,
                    interaction.guild.get_channel(
                        Config.get("Promo", {}).get("channel")
                    ),
                    interaction.message,
                )
            )
            return await interaction.followup.send(
                view=view,
                ephemeral=True,
            )

        if Selected == "Webhook":
            if not await premium(interaction.guild.id):
                return await interaction.followup.send(
                    embed=NoPremium(), view=Support()
                )

            embed = await WebhookEmbed(interaction, Config)
            view = WebButton(interaction.user)
            view.add_item(WebhookToggle(interaction.user))
            return await interaction.followup.send(
                embed=embed, view=view, ephemeral=True
            )
        if Selected == "Promotion Audit Log":
            view = discord.ui.View()

            view.add_item(
                LogChannel(
                    interaction.user,
                    interaction.guild.get_channel(
                        Config.get("Promo", {}).get("LogChannel"),
                    ),
                    interaction.message,
                )
            )
            return await interaction.followup.send(
                view=view,
                ephemeral=True,
            )
        elif Selected == "Preferences":
            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_author(
                name="Preferences",
                icon_url="https://cdn.discordapp.com/emojis/1160541147320553562.webp?size=96&quality=lossless",
            )
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.description = "> **Promotion Issuer Button:** A disabled button that displays the username of the issuer at the bottom of the promotion embed.\n> **Auto Role:** Automatically roles the user the rank you specify on the promote command.\n> **Show Issuer:** If disabled on the embeds the issuer will not be displayed. It won't work with customised embeds & it will still appear on /promotions."
            if not Config.get("Module Options"):
                Config["Module Options"] = {}
            view = Preferences(interaction.user)
            view.children[0].label = (
                f"Auto Role ({'Enabled' if Config.get('Module Options', {}).get('autorole', True) else 'Disabled'})"
            )
            view.children[0].style = (
                discord.ButtonStyle.green
                if Config.get("Module Options", {}).get("autorole", True)
                else discord.ButtonStyle.red
            )
            view.children[1].style = (
                discord.ButtonStyle.green
                if Config.get("Module Options", {}).get("promotionissuer", False)
                else discord.ButtonStyle.red
            )

            view.children[1].label = (
                f"Issuer Button Display ({'Enabled' if Config.get('Module Options', {}).get('promotionissuer', False) else 'Disabled'})"
            )
            view.children[2].style = (
                discord.ButtonStyle.green
                if Config.get("Module Options", {}).get("pshowissuer", True)
                else discord.ButtonStyle.red
            )
            view.children[2].label = (
                f"Show Issuer ({'Enabled' if Config.get('Module Options', {}).get('pshowissuer', False) else 'Disabled'})"
            )
            return await interaction.followup.send(
                embed=embed, view=view, ephemeral=True
            )
        elif Selected == "Customise Embed":
            try:
                custom = await interaction.client.db["Customisation"].find_one(
                    {"guild_id": interaction.guild.id, "type": "Promotions"}
                )
                embed = None

                from Cogs.Configuration.Components.EmbedBuilder import (
                    DisplayEmbed,
                    Embed,
                )

                view = Embed(
                    interaction.user,
                    FinalFunction,
                    "Promotions",
                    {"thumb": "{staff.avatar}", "author_url": "{author.avatar}"},
                )
                if not custom:
                    embed = discord.Embed(color=discord.Color.dark_embed())
                    embed = discord.Embed(
                        title="Staff Promotion",
                        color=0x2B2D31,
                        description="* **User:** {staff.mention}\n* **Updated Rank:** {newrank}\n* **Reason:** {reason}",
                    )
                    embed.set_thumbnail(url=interaction.user.display_avatar)
                    embed.set_author(
                        name="Signed, {author.name}",
                        icon_url=interaction.user.display_avatar,
                    )
                    view.remove_item(view.Buttons)
                    view.remove_item(view.RemoveEmbed)
                    view.remove_item(view.Content)
                    view.remove_item(view.Permissions)
                    view.remove_item(view.ForumsChannel)
                    view.remove_item(view.Ping)
                    return await interaction.edit_original_response(
                        embed=embed, view=view
                    )

                embed = await DisplayEmbed(custom, interaction.user)
                view.remove_item(view.Buttons)
                view.remove_item(view.RemoveEmbed)
                view.remove_item(view.Content)
                view.remove_item(view.Permissions)
                view.remove_item(view.ForumsChannel)
                view.remove_item(view.Ping)
                view = Embed(
                    interaction.user,
                    FinalFunction,
                    "Promotions",
                    {
                        "thumb": (
                            interaction.user.display_avatar.url
                            if custom.get("embed", {}).get("thumbnail")
                            == "{author.avatar}"
                            else (
                                "{staff.avatar}"
                                if custom.get("embed", {}).get("thumbnail")
                                == "{staff.avatar}"
                                else custom.get("embed", {}).get("thumbnail")
                            )
                        ),
                        "author_url": (
                            interaction.user.display_avatar.url
                            if custom.get("embed", {}).get("author", {}).get("icon_url")
                            == "{author.avatar}"
                            else (
                                "{staff.avatar}"
                                if custom.get("embed", {})
                                .get("author", {})
                                .get("icon_url")
                                == "{staff.avatar}"
                                else custom.get("embed", {})
                                .get("author", {})
                                .get("icon_url")
                            )
                        ),
                        "image": (
                            interaction.user.display_avatar.url
                            if custom.get("embed", {}).get("image") == "{author.avatar}"
                            else (
                                "{staff.avatar}"
                                if custom.get("embed", {}).get("image")
                                == "{staff.avatar}"
                                else custom.get("embed", {}).get("image")
                            )
                        ),
                    },
                )
                return await interaction.edit_original_response(embed=embed, view=view)
            except Exception as e:
                traceback.print_exc(e)
     
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": Config}
        )
        await interaction.response.edit_message(view=self, content=None)


async def FinalFunction(interaction: discord.Interaction, d=None):
    from Cogs.Configuration.Configuration import ConfigMenu, Options

    embed = interaction.message.embeds[0]
    if embed:
        data = {
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

    await interaction.client.db["Customisation"].update_one(
        {"guild_id": interaction.guild.id, "type": "Promotions"},
        {"$set": data},
        upsert=True,
    )
    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})

    view = discord.ui.View()
    view.add_item(
        PSelect(
            interaction.user,
        )
    )
    view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
    await interaction.response.edit_message(
        embed=await PromotionEmbed(
            interaction, Config, discord.Embed(color=discord.Color.dark_embed())
        ),
        view=view,
    )


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
            config = {"_id": interaction.guild.id, "Promo": {}}
        elif "Promo" not in config:
            config["Promo"] = {}
        elif "LogChannel" not in config.get("Promo", {}):
            config["Promo"]["LogChannel"] = None

        config["Promo"]["LogChannel"] = self.values[0].id if self.values else None
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await PromotionEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


class CoolDown(discord.ui.Modal):
    def __init__(self, author: discord.Member, message: discord.Message):
        super().__init__(title="Promotion Cooldown")
        self.author = author
        self.message = message
        self.Days = discord.ui.TextInput(
            label="How many days is this cooldown?",
            placeholder="Eg. 2. Type 0 if you don't want a cooldown.",
            required=False,
        )

        self.add_item(self.Days)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "Promo": {}}
        elif "Promo" not in config:
            config["Promo"] = {}
        elif "Cooldown" not in config.get("Promo", {}):
            config["Promo"]["Cooldown"] = None
        config["Promo"]["Cooldown"] = self.Days.value if self.Days else None
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await PromotionEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


class Preferences(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    async def ToggleOption(
        self, interaction: discord.Interaction, button: discord.ui.Button, Option: str
    ):
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {
                "Infraction": {},
                "Module Options": {},
                "_id": interaction.guild.id,
            }
        if not Config.get("Module Options"):
            Config["Module Options"] = {}

        if Config.get("Module Options", {}).get(Option, False):
            Config["Module Options"][Option] = False
            button.style = discord.ButtonStyle.red
            if Option == "promotionissuer":
                button.label = f"Issuer Button Display ({'Enabled' if Config.get('Module Options', {}).get('promotionissuer', False) else 'Disabled'})"
            elif Option == "pshowissuer":
                button.label = f"Show Issuer ({'Enabled' if Config.get('Module Options', {}).get('pshowissuer', True) else 'Disabled'})"
            elif Option == "autorole":
                button.label = f"Auto Role ({'Enabled' if Config.get('Module Options', {}).get('autorole', True) else 'Disabled'})"
        else:
            Config["Module Options"][Option] = True
            button.style = discord.ButtonStyle.green
            if Option == "promotionissuer":
                button.label = f"Issuer Button Display ({'Enabled' if Config.get('Module Options', {}).get('promotionissuer', False) else 'Disabled'})"
            elif Option == "pshowissuer":
                button.label = f"Show Issuer ({'Enabled' if Config.get('Module Options', {}).get('pshowissuer', True) else 'Disabled'})"
            elif Option == "autorole":
                button.label = f"Auto Role ({'Enabled' if Config.get('Module Options', {}).get('autorole', True) else 'Disabled'})"

        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": Config}
        )
        await interaction.response.edit_message(content=None, view=self)

    @discord.ui.button(label="Auto Role (Enabled)", style=discord.ButtonStyle.green)
    async def AutoRole(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "autorole")

    @discord.ui.button(
        label="Issuer Button Display (Disabled)", style=discord.ButtonStyle.red
    )
    async def IssuerButton(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "promotionissuer")

    @discord.ui.button(label="Show Issuer (Disable)", style=discord.ButtonStyle.green)
    async def ShowIssuer(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "pshowissuer")





class PromotionChannel(discord.ui.ChannelSelect):
    def __init__(
        self,
        author: discord.Member,
        channel: discord.TextChannel = None,
        message: discord.Message = None,
    ):
        super().__init__(
            placeholder="Promotion Channel",
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
            config = {"_id": interaction.guild.id, "Promo": {}}
        elif "Promo" not in config:
            config["Promo"] = {}

        config["Promo"]["channel"] = self.values[0].id if self.values else None
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await PromotionEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


class WebhookDesign(discord.ui.Modal):
    def __init__(self, author: discord.Member):
        super().__init__(title="Webhook Design")
        self.author = author
        self.username = discord.ui.TextInput(
            label="Username", placeholder="The username of the webhook"
        )
        self.AvatarURL = discord.ui.TextInput(
            label="Avatar Link",
            placeholder="A avatar link, I recommend using something like Imgur.",
        )
        self.add_item(self.username)
        self.add_item(self.AvatarURL)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        if not await premium(interaction.guild.id):
            return await interaction.response.send_message(
                embed=NoPremium(), view=Support()
            )
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if Config is None:
            Config = {"_id": interaction.guild.id, "Promo": {"Webhook": {}}}
        if "Promo" not in Config:
            Config["Promo"] = {}
        if "Webhook" not in Config["Promo"]:
            Config["Promo"]["Webhook"] = {}
        if not self.AvatarURL.value.strip():
            self.AvatarURL.value = interaction.client.user.display_avatar.url
        AV = self.AvatarURL.value.strip()
        pattern = r"^https?://.*\.(png|jpg|jpeg|gif|webp)(\?.*)?$"
        if not re.match(pattern, AV, re.IGNORECASE):
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** the avatar link provided is not a valid image URL!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        Config["Promo"]["Webhook"] = {
            "Username": self.username.value,
            "Avatar": self.AvatarURL.value,
        }
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": Config}
        )
        await interaction.response.edit_message(
            embed=await WebhookEmbed(interaction, Config)
        )


class WebhookToggle(discord.ui.Select):
    def __init__(self, author: discord.Member):
        options = [
            discord.SelectOption(
                label="Enable",
                value="enable",
            ),
            discord.SelectOption(label="Disable", value="disable"),
        ]
        super().__init__(
            placeholder="Select", min_values=1, max_values=1, options=options
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {"Promo": {}, "_id": interaction.guild.id}
        if "Promo" not in Config:
            Config["Promo"] = {}
        if "Webhook" not in Config["Promo"]:
            Config["Promo"]["Webhook"] = {}
        if "Enabled" not in Config["Promo"]["Webhook"]:
            Config["Promo"]["Webhook"]["Enabled"] = False

        selection = self.values[0]
        if selection == "enable":

            Config["Promo"]["Webhook"]["Enabled"] = True
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$set": Config}
            )
            await interaction.response.edit_message(
                embed=await WebhookEmbed(interaction, Config)
            )

        elif selection == "disable":
            Config["Promo"]["Webhook"]["Enabled"] = False
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$set": Config}
            )

            await interaction.response.edit_message(
                embed=await WebhookEmbed(interaction, Config)
            )


class WebButton(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(
        label="Customise Webhook", style=discord.ButtonStyle.blurple, row=3
    )
    async def B(self, I: discord.Interaction, B: discord.ui.Button):
        await I.response.send_modal(WebhookDesign(self.author))


async def WebhookEmbed(interaction: discord.Interaction, Config: dict):
    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not Config:
        Config = {"Promo": {}, "_id": interaction.guild.id}

    embed = discord.Embed()
    embed.set_author(
        name="Webhook",
        icon_url="https://cdn.discordapp.com/emojis/1400197752339824821.webp?size=96",
    )
    WebhookSettings = Config.get("Promo", {}).get("Webhook", {})
    enabled = WebhookSettings.get("Enabled", False)
    username = WebhookSettings.get("Username", None) or "Not Set"
    avatar = WebhookSettings.get("Avatar", None) or "Not Set"
    embed.add_field(
        name="<:Webhook:1400197752339824821> Webhook Settings",
        value=f"> {replytop} **Enabled:** {'True' if enabled else 'False'}\n> {replymiddle} **Username:** {username}\n> {replybottom} **Avatar:** {avatar}",
    )
    return embed


async def PromotionEmbed(
    interaction: discord.Interaction, Config: dict, embed: discord.Embed
):
    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not Config:
        Config = {"Promo": {}, "_id": interaction.guild.id}
    Channel = (
        interaction.guild.get_channel(Config.get("Promo", {}).get("channel"))
        or "Not Configured"
    )
    Promo = Config.get("Promo", {})
    Cooldown = Promo.get("Cooldown")
    Days = f"{Cooldown} Days" if Cooldown is not None else "Not Set"
    if isinstance(Channel, discord.TextChannel):
        Channel = Channel.mention

    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> This is where you can manage your server's promotion settings! Promotions are a way to give staff members more power. You can find out more at [the documentation](https://docs.astrobirb.dev/Modules/promotions)."
    embed.add_field(
        name="<:settings:1207368347931516928> Promotions",
        value=f"> {replytop} `Promotion Channel:` {Channel}\n> {replybottom} `Cooldown:` {Days}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev/Modules/promotions).",
        inline=False,
    )
    return embed
