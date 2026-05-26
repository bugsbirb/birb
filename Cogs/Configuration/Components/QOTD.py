import discord
from utils.emojis import *
from datetime import datetime, timedelta
import re
import io
from utils.permissions import premium
from utils.HelpEmbeds import NoPremium, Support, NotYourPanel


class QOTDOptions(discord.ui.Select):
    def __init__(self, author: discord.Member, options: list):

        super().__init__(options=options)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        option = self.values[0]
        from Cogs.Configuration.Configuration import ConfigMenu, Options, Reset

        Config = await interaction.client.db["Config"].find_one(
            {"_id": interaction.guild.id}
        )

        await Reset(
            interaction,
            lambda: QOTDOptions(interaction.user, self.options),
            lambda: ConfigMenu(Options(Config), interaction.user),
        )

        if option == "Start QOTD":
            await interaction.client.db["qotd"].update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {"nextdate": datetime.now() + timedelta(days=1)}},
                upsert=True,
            )
            nextdate = datetime.now() + timedelta(days=1)
            timestamp = f"<t:{int(nextdate.timestamp())}>"
            embed = discord.Embed(
                title=f"{greencheck} Enabled",
                description=f"> **Next Post Date:** {timestamp}",
                color=discord.Color.brand_green(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            options = [
                discord.SelectOption(
                    label="Stop QOTD",
                    emoji="<:stop:1330484991414501418>",
                    description="End the daily questions.",
                ),
                discord.SelectOption(
                    label="Channel", emoji="<:tag:1234998802948034721>"
                ),
                discord.SelectOption(
                    label="Webhook",
                    description="Send it as a webhook.",
                    emoji="<:Webhook:1400197752339824821>",
                ),
                discord.SelectOption(label="Ping", emoji="<:Ping:1298301862906298378>"),
                discord.SelectOption(
                    label="Preferences", emoji="<:leaf:1160541147320553562>"
                ),
            ]
            view = discord.ui.View()
            view.add_item(QOTDOptions(self.author, options))
            view.add_item(
                ConfigMenu(
                    Options(
                        await interaction.client.config.find_one(
                            {"_id": interaction.guild.id}
                        )
                    ),
                    interaction.user,
                )
            )
            await interaction.edit_original_response(
                embed=await QOTDEMbed(
                    interaction, discord.Embed(color=discord.Color.dark_embed())
                ),
                view=view,
            )
        elif option == "Custom Questions":
            if not await premium(interaction.guild.id):
                return await interaction.followup.send(
                    embed=NoPremium(), view=Support(), ephemeral=True
                )
            view = CustomQuestions(interaction.user)
            current = Config.get("QOTD", {}).get("Premade", True)
            if current:
                view.Premade.label = "Premade Questions: Enabled"
                view.Premade.style = discord.ButtonStyle.green
            else:
                view.Premade.label = "Premade Questions: Disabled"
                view.Premade.style = discord.ButtonStyle.red

            await interaction.followup.send(
                files=[await customQuestionsMessage(interaction)],
                view=view,
                ephemeral=True
            )
        elif option == "Webhook":
            if not await premium(interaction.guild.id):
                return await interaction.followup.send(
                    embed=NoPremium(), view=Support()
                )

            Config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )

            embed = await WebhookEmbed(interaction, Config)
            view = WebButton(interaction.user)
            view.add_item(WebhookToggle(interaction.user))
            return await interaction.followup.send(
                embed=embed, view=view, ephemeral=True
            )

        elif option == "Stop QOTD":

            await interaction.client.db["qotd"].update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {"nextdate": None}},
                upsert=True,
            )
            embed = discord.Embed(
                title=f"{redx} Disabled",
                description="> **QOTD has been disabled.**",
                color=discord.Color.brand_red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            options = [
                discord.SelectOption(
                    label="Start QOTD",
                    emoji="<:start:1299717567660687371>",
                    description="Start the daily questions. (Pressing this while its already started will restart it.)",
                ),
                discord.SelectOption(
                    label="Channel", emoji="<:tag:1234998802948034721>"
                ),
                discord.SelectOption(
                    label="Webhook",
                    description="Send it as a webhook.",
                    emoji="<:Webhook:1400197752339824821>",
                ),
                discord.SelectOption(label="Ping", emoji="<:Ping:1298301862906298378>"),
                discord.SelectOption(
                    label="Preferences", emoji="<:leaf:1160541147320553562>"
                ),
            ]

            view = discord.ui.View()
            view.add_item(QOTDOptions(self.author, options))
            view.add_item(
                ConfigMenu(
                    Options(
                        await interaction.client.config.find_one(
                            {"_id": interaction.guild.id}
                        )
                    ),
                    interaction.user,
                )
            )

            await interaction.edit_original_response(
                embed=await QOTDEMbed(
                    interaction, discord.Embed(color=discord.Color.dark_embed())
                ),
                view=view,
            )

        elif option == "Channel":

            Config = await interaction.client.db["qotd"].find_one(
                {"_id": interaction.guild.id}
            )
            if not Config:
                Config = {"_id": interaction.guild.id, "channel": None}
            view = discord.ui.View()
            view.add_item(
                QOTDChannel(
                    self.author,
                    (
                        [interaction.guild.get_channel(Config.get("channel"))]
                        if Config.get("channel")
                        else []
                    ),
                    interaction.message,
                )
            )
            await interaction.followup.send(view=view, ephemeral=True)
        elif option == "Preferences":
            Config = await interaction.client.db["qotd"].find_one(
                {"guild_id": interaction.guild.id}
            )
            if not Config:
                Config = {"guild_id": interaction.guild.id, "qotdthread": True}
            view = Preferences(self.author)
            if Config.get("qotdthread"):
                view.IssuerButton.label = "Threads (Enabled)"
                view.IssuerButton.style = discord.ButtonStyle.green
            else:
                view.IssuerButton.label = "Threads (Disabled)"
                view.IssuerButton.style = discord.ButtonStyle.red

            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.description = "> - **Threads:** If enabled, the bot will create a thread for each QOTD post. This is useful for keeping the discussion organized."

            embed.set_author(
                name="Preferences",
                icon_url="https://cdn.discordapp.com/emojis/1160541147320553562.webp?size=96&quality=lossless",
            )
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        elif option == "Ping":
            view = discord.ui.View()
            view.add_item(PingRole(interaction.user, interaction.message))
            await interaction.followup.send(view=view, ephemeral=True)


class CreateQuestion(discord.ui.Modal):
    def __init__(self, author: discord.Member):
        super().__init__(title="Create Question")
        self.author = author
        self.question = discord.ui.TextInput(
            label="Question",
            placeholder="Enter the question of the day",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=500,
        )
        self.add_item(self.question)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        await interaction.client.db["Question Database"].insert_one(
            {
                "guild": interaction.guild.id,
                "question": self.question.value.strip(),
                "createdBy": interaction.user.id,
                "createdAt": datetime.now(),
            }
        )
        await interaction.response.edit_message(
            attachments=[await customQuestionsMessage(interaction)],
        )


class DeleteQuestion(discord.ui.Modal):
    def __init__(self, author: discord.Member):
        super().__init__(title="Delete Question")
        self.author = author
        self.question = discord.ui.TextInput(
            label="Question (exact)",
            placeholder="Paste the exact question text to delete",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=500,
        )
        self.add_item(self.question)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        Question = self.question.value.strip()
        result = await interaction.client.db["Question Database"].delete_one(
            {"guild": interaction.guild.id, "question": Question}
        )
        if result.deleted_count == 0:
            return await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name}**, no question matched that exact text.",
                ephemeral=True,
            )

        await interaction.response.edit_message(
            attachments=[await customQuestionsMessage(interaction)],
        )


class CustomQuestions(discord.ui.View):
    def __init__(self, author: discord.Member, config=None):
        super().__init__(timeout=1600)
        self.author = author
        self.config = config
    
    @discord.ui.button(label="Create", style=discord.ButtonStyle.green)
    async def Create(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.response.send_modal(CreateQuestion(self.author))

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red)
    async def Delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.response.send_modal(DeleteQuestion(self.author))

    @discord.ui.button(label="Premade Questions: Enabled")
    async def Premade(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        Config = await interaction.client.db["Config"].find_one(
            {"_id": interaction.guild.id}
        )
        if not Config:
            Config = {"_id": interaction.guild.id, "QOTD": {}}
        if "QOTD" not in Config:
            Config["QOTD"] = {}

        current = Config["QOTD"].get("Premade", True)
        new = not current
        Config["QOTD"]["Premade"] = new

        await interaction.client.db["Config"].update_one(
            {"_id": interaction.guild.id}, {"$set": {"QOTD": Config["QOTD"]}}, upsert=True
        )

        if new:
            button.label = "Premade Questions: Enabled"
            button.style = discord.ButtonStyle.green
        else:
            button.label = "Premade Questions: Disabled"
            button.style = discord.ButtonStyle.red

        await interaction.response.edit_message(attachments=[await customQuestionsMessage(interaction)], view=self)



class PingRole(discord.ui.RoleSelect):
    def __init__(
        self,
        author: discord.Member,
        message: discord.Message = None,
    ):
        super().__init__(
            min_values=0,
            max_values=1,
        )
        self.author = author
        self.message = message

    async def callback(self, interaction):
        from Cogs.Configuration.Configuration import ConfigMenu, Options

        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        await interaction.client.db["qotd"].update_one(
            {"guild_id": interaction.guild.id},
            {
                "$set": {
                    "pingrole": (
                        self.values[0].id
                        if self.values
                        else None if self.values else None
                    ),
                    "guild_id": interaction.guild_id,
                }
            },
            upsert=True,
        )
        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await QOTDEMbed(
                    interaction, discord.Embed(color=discord.Color.dark_embed())
                ),
            )
        except:
            pass


class QOTDChannel(discord.ui.ChannelSelect):
    def __init__(self, author, channels, msg):
        super().__init__(
            placeholder="Channel",
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
            default_values=channels,
        )
        self.author = author
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.client.db["qotd"].update_one(
            {"guild_id": interaction.guild.id},
            {
                "$set": {
                    "channel_id": self.values[0].id if self.values else None,
                    "guild_id": interaction.guild_id,
                }
            },
            upsert=True,
        )
        await self.msg.edit(
            embed=await QOTDEMbed(
                interaction, discord.Embed(color=discord.Color.dark_embed())
            )
        )
        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name},** channel has been updated.",
            view=None,
            embed=None,
        )


class Preferences(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    async def ToggleOption(
        self, interaction: discord.Interaction, button: discord.ui.Button, Option: str
    ):
        QOTD = await interaction.client.db["qotd"].find_one(
            {"guild_id": interaction.guild.id}
        )
        if not QOTD:
            QOTD = {"guild_id": interaction.guild.id, "qotdthread": True}

        if Option == "qotdthread":
            if QOTD.get("qotdthread", True):
                QOTD["qotdthread"] = False
                self.IssuerButton.label = "Threads (Disabled)"
                self.IssuerButton.style = discord.ButtonStyle.red
            else:
                QOTD["qotdthread"] = True
                self.IssuerButton.label = "Threads (Enabled)"
                self.IssuerButton.style = discord.ButtonStyle.green

        await interaction.client.db["qotd"].update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"qotdthread": QOTD["qotdthread"]}},
            upsert=True,
        )
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Threads (Enabled)", style=discord.ButtonStyle.green)
    async def IssuerButton(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "qotdthread")


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
            Config = {"_id": interaction.guild.id, "QOTD": {"Webhook": {}}}

        if "QOTD" not in Config:
            Config["QOTD"] = {}
        if "Webhook" not in Config["QOTD"]:
            Config["QOTD"]["Webhook"] = {}

        if self.AvatarURL is None:
            self.AvatarURL = interaction.client.user.display_avatar.url
        AV = self.AvatarURL.value.strip()
        pattern = r"^https?://.*\.(png|jpg|jpeg|gif|webp)(\?.*)?$"
        if not re.match(pattern, AV, re.IGNORECASE):
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** the avatar link provided is not a valid image URL!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        Config["QOTD"]["Webhook"] = {
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
            Config = {"QOTD": {}, "_id": interaction.guild.id}
        if "QOTD" not in Config:
            Config["QOTD"] = {}
        if "Webhook" not in Config["QOTD"]:
            Config["QOTD"]["Webhook"] = {}
        if "Enabled" not in Config["QOTD"]["Webhook"]:
            Config["QOTD"]["Webhook"]["Enabled"] = False
        selection = self.values[0]
        if selection == "enable":
            if "Webhook" not in Config["QOTD"]:
                Config["QOTD"]["Webhook"] = {}
            Config["QOTD"]["Webhook"]["Enabled"] = True
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$set": Config}
            )
            await interaction.response.edit_message(
                embed=await WebhookEmbed(interaction, Config)
            )

        elif selection == "disable":
            if "Webhook" not in Config["QOTD"]:
                Config["QOTD"]["Webhook"] = {}
            Config["QOTD"]["Webhook"]["Enabled"] = False
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
        Config = {"QOTD": {}, "_id": interaction.guild.id}

    embed = discord.Embed()
    embed.set_author(
        name="Webhook",
        icon_url="https://cdn.discordapp.com/emojis/1400197752339824821.webp?size=96",
    )
    WebhookSettings = Config.get("QOTD", {}).get("Webhook", {})
    enabled = WebhookSettings.get("Enabled", False)
    username = WebhookSettings.get("Username", None) or "Not Set"
    avatar = WebhookSettings.get("Avatar", None) or "Not Set"
    embed.add_field(
        name="<:Webhook:1400197752339824821> Webhook Settings",
        value=f"> {replytop} **Enabled:** {'True' if enabled else 'False'}\n> {replymiddle} **Username:** {username}\n> {replybottom} **Avatar:** {avatar}",
    )
    return embed


async def QOTDEMbed(interaction: discord.Interaction, embed: discord.Embed):
    config = await interaction.client.db["qotd"].find_one(
        {"guild_id": interaction.guild.id}
    )
    channel = (
        interaction.guild.get_channel(config.get("channel_id") if config else 0)
        or "Not Configured"
    )
    NextDate = config.get("nextdate") if config else None
    if NextDate:
        NextDate = f"<t:{int(NextDate.timestamp())}>" or "Not Active"
    else:
        NextDate = "Not Active"

    if isinstance(channel, discord.TextChannel):
        channel = channel.mention
    ping = (
        f'<@&{config.get("pingrole")}>'
        if config and config.get("pingrole")
        else "Not Configured"
    )

    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> This is where you can manage your server's QOTD settings! QOTD is a way for members to answer a question of the day. You can find out more at [the documentation](https://docs.astrobirb.dev/Modules/qotd)."
    embed.add_field(
        name="<:settings:1207368347931516928> Daily Questions",
        value=f"{replytop} `Channel:` {channel}\n{replymiddle} `Ping`: {ping}\n{replybottom} `Next Date:` {NextDate}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev/Modules/qotd).",
        inline=False,
    )
    return embed


async def customQuestionsMessage(interaction: discord.Interaction):
    guildQuestions = (
        await interaction.client.db["Question Database"]
        .find({"guild": interaction.guild.id})
        .to_list(length=None)
    )
    listedQuestions = [guild.get("question") for guild in guildQuestions]
    text = "\n".join(c for c in listedQuestions if c)
    fp = io.BytesIO(text.encode("utf-8"))
    return discord.File(fp=fp, filename="Questions.txt")
