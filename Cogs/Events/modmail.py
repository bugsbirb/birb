import discord
from discord.ext import commands
from datetime import datetime, timedelta


from utils.emojis import *
import chat_exporter
import traceback
import random
import io


async def Reply(
    self: commands.Bot,
    message: discord.Message,
    Config: dict,
    ModmailData: dict,
    Guild: discord.Guild,
):
    try:
        Channel = await Guild.fetch_channel(int(ModmailData.get("channel_id", 0)))
    except (discord.NotFound, discord.HTTPException):
        traceback.format_exc(e)
        return await self.db["modmail"].delete_one({"user_id": message.author.id})
    if not Channel:
        return await message.add_reaction("⚠️")

    embed = discord.Embed(
        color=discord.Color.dark_embed(),
        title=f"{message.author}",
        description=f"```{message.content}```",
    )
    embed.set_author(name=Guild.name, icon_url=Guild.icon)
    embed.set_thumbnail(url=Guild.icon)

    files = None
    if message.attachments:
        files = [await file.to_file() for file in message.attachments]

    if Config.get("Module Options", {}):
        if Config.get("Module Options").get("MessageFormatting") == "Messages":
            try:
                await Channel.send(
                    f"<:messagereceived:1201999712593383444> {message.author.name}: {message.content}",
                    files=files,
                )
            except Exception as e:
                print(e)
                return await message.add_reaction("⚠️")
            return await message.add_reaction("📨")
    try:
        await Channel.send(embed=embed, files=files)
    except Exception as e:
        print(e)
        return await message.add_reaction("⚠️")
    return await message.add_reaction("📨")


async def Close(interaction: discord.Interaction, reason=None):
    Text = None
    TranscriptMSG = None
    msg = await interaction.followup.send(
        content="<a:Loading:1167074303905386587> Closing..."
    )
    # // Commit Modmail Discovery QWEo0p9;aSJDOPAHJSOp'd
    if isinstance(interaction.channel, discord.DMChannel):
        Modmail = await interaction.client.db["modmail"].find_one(
            {"user_id": interaction.user.id}
        )
    else:
        Modmail = await interaction.client.db["modmail"].find_one(
            {"channel_id": interaction.channel.id}
        )
    if not Modmail:
        return await msg.edit(
            content=f"  **{interaction.user.display_name},** you have no active modmail."
        )
    Server = await interaction.client.fetch_guild(Modmail.get("guild_id"))
    if not Server:
        return await msg.edit(
            content=f"  **{interaction.user.display_name},** no idea how but the guild can't be found from the modmail????"
        )
    Config = await interaction.client.config.find_one({"_id": Server.id})
    if not Config:
        return await msg.edit(
            content=f"  **{interaction.user.display_name},** the bot isn't set up. Run `/config`."
        )
    if not Config.get("Modmail"):
        return await msg.edit(
            content=f"  **{interaction.user.display_name},** you haven't set up the modmail module."
        )
    ModmailType = Config.get("Module Options", {}).get("ModmailType", "channel")
    channel = interaction.client.get_channel(int(Modmail.get("channel_id")))

    channelcreated = f"{channel.created_at.strftime('%d/%m/%Y')}"
    TranscriptID = random.randint(100, 50000)

    # // Commit Modmail Extermination
    await interaction.client.db["modmail"].delete_one({"user_id": interaction.user.id})
    if channel and ModmailType == "channel":
        Text = ""
        async for message in channel.history(limit=None, oldest_first=True):

            text = message.content
            author = message.author.name
            if not text and message.embeds:
                embed = message.embeds[0]
                if embed.title:
                    author = embed.title

                if embed.description:
                    text = embed.description.strip("`")
                else:
                    text = "No content"
            time = message.created_at.strftime("%d/%m/%Y %H:%M:%S")
            Text += f"{time} | @{author}: {text}\n"
        if ModmailType == "channel":
            try:
                await channel.delete()

            except discord.Forbidden:
                await msg.edit(
                    content=f"  **{interaction.user.display_name},** I can't delete this channel please contact the server admins.",
                )
                return
    user = await interaction.client.fetch_user(Modmail.get("user_id"))
    if reason is None:
        reason = "No reason provided."
    embed = discord.Embed(
        title="Modmail Closed",
        description=f"",
        color=discord.Color.dark_embed(),
    )
    embed.set_author(
        name=Server.name,
        icon_url=Server.icon,
    )
    embed.add_field(
        name="<:Document:1191926049857097748> ID",
        value=TranscriptID,
        inline=True,
    )
    embed.add_field(
        name="<:Add:1163095623600447558> Opened",
        value=user.mention,
        inline=True,
    )
    embed.add_field(
        name="<:Exterminate:1223063042246443078> Closed",
        value=interaction.user.mention,
        inline=True,
    )
    embed.add_field(
        name="<:casewarningwhite:1191903691750514708> Time Created",
        value=channelcreated,
        inline=True,
    )
    embed.add_field(
        name="<:reason:1235000513477738576> Reason",
        value=reason,
        inline=True,
    )

    if channel and Modmail.get("DMMsg"):
        try:
            Author = await interaction.client.fetch_user(int(Modmail.get("user_id")))
            DMMessage = await Author.fetch_message(int(Modmail.get("DMMsg")))
            if DMMessage and Author:
                await DMMessage.unpin()
                view = ModmailClosure()
                view.close.disabled = True
                view.close.label = "Closed"
                await DMMessage.edit(embed=embed, view=view)
        except (discord.NotFound, discord.HTTPException):
            pass

        if (
            Config.get("Modmail", {}).get("transcripts")
            and not ModmailType == "threads"
        ):
            if Modmail.get("Category"):
                CategoryData = (
                    Config.get("Modmail", {})
                    .get("Categories", {})
                    .get(Modmail.get("Category"), {})
                )

                try:
                    TranscriptChannel = await interaction.client.fetch_channel(
                        CategoryData.get("transcript")
                    )
                except (discord.NotFound, discord.HTTPException):
                    return await msg.edit(
                        content=f"  **{interaction.user.display_name},** you have setup the transcript channel but it can't be found.",
                    )
                view = Links()
                try:
                    TranscriptMSG = await TranscriptChannel.send(embed=embed, view=view)
                except:
                    pass
            else:
                try:
                    TranscriptChannel = await interaction.client.fetch_channel(
                        Config.get("Modmail", {}).get("transcripts")
                    )
                except (discord.NotFound, discord.HTTPException):
                    return await msg.edit(
                        content=f"  **{interaction.user.display_name},** you have setup the transcript channel but it can't be found.",
                    )
                view = Links()
                try:
                    TranscriptMSG = await TranscriptChannel.send(embed=embed, view=view)
                except:
                    pass

    await interaction.client.db["Transcripts"].insert_one(
        {
            "transcriptid": TranscriptID,
            "guild_id": Server.id,
            "closedby": interaction.user.id,
            "reason": reason,
            "author": user.id,
            "timestamp": datetime.now(),
            "transcript": TranscriptMSG.id if TranscriptMSG else None,
            "text": Text if Text else "Nothin",
        }
    )
    if ModmailType == "channel":
        await msg.delete()
    else:
        try:
            await channel.send(
                content=f"<:close:1280576608125849731> The modmail has been closed. This thread will be archived and locked.\n-# Locked by @{user.name}"
            )
            await msg.delete()
            await channel.edit(archived=True, locked=True)
        except (discord.Forbidden, discord.HTTPException):
            print("[Modmail Skill Issue] couldn't lock the thread or anything.")
            if msg:
                try:
                    await msg.add_reaction("⚠️")
                except:
                    pass


class Links(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Generate Transcript",
        style=discord.ButtonStyle.success,
        emoji="<:utility:1234994834763419769>",
        custom_id="Generate Transcript",
    )
    async def generate_transcript(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        Modmail = await interaction.client.db["Transcripts"].find_one(
            {"transcript": interaction.message.id}
        )
        if not Modmail:
            return await interaction.followup.send(
                content=f"  **{interaction.user.display_name},** you have no active modmail."
            )
        if Modmail.get("text"):
            Text = Modmail.get("text")
            if not isinstance(Text, str):
                return await interaction.followup.send(
                    content=f"  **{interaction.user.display_name},** this isn't a valid transcript."
                )
            file = discord.File(io.BytesIO(Text.encode()), filename="transcript.txt")
            await interaction.followup.send(file=file, ephemeral=True)
        else:
            await interaction.followup.send(
                content=f"  **{interaction.user.display_name},** there is no transcript to generate.",
                ephemeral=True,
            )


class Select(discord.ui.Select):
    def __init__(
        self, author: discord.Member, message: discord.Message, Options: list = []
    ):
        super().__init__(options=Options)
        self.author = author
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            Guild = await interaction.client.fetch_guild(self.values[0])
        except (discord.NotFound, discord.HTTPException):
            return await interaction.followup.send(
                f"  **{interaction.user.display_name},** I can't find the server anymore.",
                ephemeral=True,
            )

        if not Guild:
            return await interaction.followup.send(
                f"  **{interaction.user.display_name},** I can't find the server anymore.",
                ephemeral=True,
            )

        Blacklists = await interaction.client.db["modmailblacklists"].find_one(
            {"guild_id": Guild.id}
        )
        if Blacklists and interaction.user.id in Blacklists.get("blacklist", []):
            return interaction.followup.send(
                f"  **{interaction.user.display_name},** you are blacklisted from using modmail in this server.",
                ephemeral=True,
            )

        Modmail = await interaction.client.db["modmail"].find_one(
            {"user_id": interaction.user.id}
        )
        if Modmail:
            return await interaction.edit_original_response(
                content=f"  {interaction.user.display_name}, you've already started a Modmail, calm down.",
                embed=None,
                view=None,
            )

        Config = await interaction.client.config.find_one({"_id": Guild.id})
        if not Config or not Config.get("Modmail"):
            return await interaction.followup.send(
                f"  **{interaction.user.display_name},** this server doesn't even have the bot setup how did you even get this?",
                ephemeral=True,
            )

        Member = await Guild.fetch_member(interaction.user.id)

        if (
            Config.get("Modmail", {}).get("Categories", [])
            and len(Config.get("Modmail", {}).get("Categories", [])) > 0
        ):
            Categories = Config.get("Modmail", {}).get("Categories", {})
            CategoryOptions = []
            for name, data in Categories.items():
                CategoryOptions.append(
                    discord.SelectOption(
                        label=name, value=name, emoji="<:category:1248312604733210735>"
                    )
                )
                if len(CategoryOptions) < 25:
                    continue
            view = discord.ui.View()
            view.add_item(
                CategorySelection(Member, self.message, CategoryOptions, Guild)
            )

            embed = discord.Embed(
                color=discord.Color.dark_embed(), title="Modmail Conversation"
            )
            embed.set_author(
                name="Modmail Selection",
                icon_url="https://cdn.discordapp.com/emojis/1298665792950374410.webp?size=96&quality=lossless",
            )
            embed.description = "Select why you are opening this modmail below."
            print("here 2")
            await interaction.edit_original_response(view=view, embed=embed)
        else:
            try:
                Category = interaction.client.get_channel(
                    int(Config.get("Modmail", {}).get("category", 0))
                )
            except (discord.NotFound, discord.HTTPException):
                return await interaction.edit_original_response(
                    content=f"  **{interaction.user.display_name},** I can't create a channel in this category. Please check my permissions.",
                    embed=None,
                    view=None,
                )
            if not Category:
                return await interaction.edit_original_response(
                    content=f"  **{interaction.user.display_name},** I can't create a channel in this category. Please check my permissions.",
                    embed=None,
                    view=None,
                )
            await OpenModmail(
                interaction, Guild, Config, Member, Category, self.message
            )


class CategorySelection(discord.ui.Select):
    def __init__(self, Member, message, Options, guild: discord.Guild):
        super().__init__(options=Options)
        self.Member = Member
        self.message = message
        self.guild = guild

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        Config = await interaction.client.config.find_one({"_id": self.guild.id})
        if not Config:
            return await interaction.followup.send(
                f"  **{interaction.user.display_name},** this server doesn't have modmail setup."
            )

        CategoryConfig = (
            Config.get("Modmail", {})
            .get("Categories", {})
            .get(interaction.data["values"][0], {})
        )
        if not CategoryConfig:
            return await interaction.followup.send(
                f"  **{interaction.user.display_name},** this category doesn't have anything setup."
            )

        Config["Modmail"] = {
            "category": CategoryConfig.get(
                "category", Config["Modmail"].get("category")
            ),
            "transcripts": CategoryConfig.get(
                "transcript", Config["Modmail"].get("transcripts")
            ),
            "ping": CategoryConfig.get("ping", Config["Modmail"].get("ping", [])),
            "threads": CategoryConfig.get(
                "threads", Config["Modmail"].get("threads", [])
            ),
        }
        Category = interaction.client.get_channel(
            int(CategoryConfig.get("category", Config["Modmail"].get("category")))
        )

        await OpenModmail(
            interaction,
            self.guild,
            Config,
            self.Member,
            Category,
            self.message,
            interaction.data["values"][0],
        )


async def OpenModmail(
    interaction: discord.Interaction,
    Guild: discord.Guild,
    Config: dict,
    Member: discord.Member,
    Category: discord.CategoryChannel = None,
    message: discord.Message = None,
    Categoriesed: str = None,
):
    embed = discord.Embed(
        color=discord.Color.dark_embed(), title="Modmail Conversation"
    )
    embed.set_author(
        name=f"@{interaction.user.name}", icon_url=interaction.user.display_avatar
    )
    embed.description = f"{replytop} **User:** {interaction.user.mention} (`{interaction.user.id}`)\n{replybottom} **Created/Joined**: <t:{int(Member.created_at.timestamp())}:R> • <t:{int(Member.joined_at.timestamp())}:R>"
    Roles = " ".join(
        [role.mention for role in Member.roles if role != Guild.default_role][:20]
    )
    if Categoriesed:
        embed.set_footer(text=Categoriesed)
    embed.add_field(value=Roles, name="Roles")
    Role = (
        Config.get("Modmail", {}).get("ping", [])[0]
        if Config.get("Modmail", {}).get("ping")
        else []
    )

    if not isinstance(Role, list):
        Role = Config.get("Modmail", {}).get("ping", [])
    if Config.get("Module Options", {}).get("ModmailType", "channel") == "channel":
        try:
            Channel = await Category.create_text_channel(
                name=f"modmail-{interaction.user.name}"
            )
            Client = await Guild.fetch_member(interaction.client.user.id)
            try:
                await Channel.set_permissions(
                    target=Client,
                    read_messages=True,
                    send_messages=True,
                    manage_channels=True,
                    manage_permissions=True,
                )
            except Exception as e:
                pass

        except (discord.Forbidden, discord.HTTPException):
            return await interaction.edit_original_response(
                content=f"  **{interaction.user.display_name},** I can't create a channel in this category. Please check my permissions.",
                embed=None,
                view=None,
            )
    else:
        try:
            Channel = await interaction.client.fetch_channel(
                int(Config.get("Modmail", {}).get("threads", 0))
            )
        except:
            return await interaction.edit_original_response(
                content=f"  **{interaction.user.display_name},** I can't find their threads channel.",
                embed=None,
                view=None,
            )

        if not Channel:
            return await interaction.edit_original_response(
                content=f"  **{interaction.user.display_name},** I can't find their threads channel.",
                embed=None,
                view=None,
            )

    ModmailRoles = [f"<@&{int(roleid)}>" for roleid in Role]
    msg = await Channel.send(
        content=", ".join(ModmailRoles) if Role else "",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(roles=True),
    )
    if (
        msg
        and Config.get("Module Options", {}).get("ModmailType", "channel") == "threads"
    ):
        Channel = await msg.create_thread(name=f"modmail-{interaction.user.name}")

    ModmailData = {
        "user_id": interaction.user.id,
        "guild_id": Guild.id,
        "channel_id": Channel.id,
        "DMMsg": interaction.message.id,
    }
    if Categoriesed:
        ModmailData["Category"] = Categoriesed
    await interaction.client.db["modmail"].insert_one(ModmailData)
    await Reply(
        interaction.client,
        message=message,
        Config=Config,
        ModmailData=ModmailData,
        Guild=Guild,
    )
    await interaction.edit_original_response(
        content=None,
        embed=discord.Embed(
            description=f"Your message has been sent to **{Guild.name}**. Please wait patiently for them to respond.",
            color=discord.Color.brand_green(),
        ).set_author(name=Guild.name, icon_url=Guild.icon),
        view=ModmailClosure(),
    )
    await interaction.message.pin()


class ModmailClosure(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.danger,
        emoji="<:close:1280576608125849731>",
        custom_id="ADosajdopsajdop",
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await Close(interaction)


class ModmailEvent(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.LastSelection = {}

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel):
        Modmail = await self.client.db["modmail"].find_one({"channel_id": channel.id})
        if not Modmail:
            return
        await self.client.db["modmail"].delete_one({"channel_id": channel.id})

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if await self.client.db["Appeal Sessions"].find_one(
            {"user_id": message.author.id}
        ):
            return
        Modmail = await self.client.db["modmail"].find_one(
            {"user_id": message.author.id}
        )
        if isinstance(message.channel, discord.DMChannel):
            if not Modmail:
                Message = await message.reply(
                    content="<a:Loading:1167074303905386587> Wait..."
                )
                try:
                    LastSelect = self.LastSelection.get(message.author.id, None)
                    if LastSelect is None:

                        self.LastSelection[message.author.id] = datetime.utcnow()
                        Remaining = timedelta(seconds=0)
                    else:
                        Remaining = timedelta(seconds=20) - (
                            datetime.utcnow() - LastSelect
                        )
                    if Remaining.total_seconds() > 0:
                        await Message.edit(
                            content=f"  **{message.author.display_name},** Please wait {int(Remaining.total_seconds())} seconds before opening another modmail panel."
                        )
                        return
                    Mutual = []
                    for guilds in self.client.guilds:
                        member = discord.utils.get(guilds.members, id=message.author.id)
                        if not member:
                            continue
                        Config = await self.client.config.find_one({"_id": guilds.id})
                        if (
                            Config
                            and Config.get("Modules", {}).get("Modmail") == True
                            and Config.get("Modmail", {}).get("category")
                        ):
                            Mutual.append(guilds)
                    if len(Mutual) == 0:
                        return await Message.edit(
                            content=f"  **{message.author.display_name},** you aren't in any mutual servers with modmail enabled."
                        )
                    Options = []
                    for Guild in Mutual:
                        Options.append(
                            discord.SelectOption(
                                label=Guild.name,
                                value=Guild.id,
                                description=f"{Guild.member_count} members",
                            )
                        )
                    if len(Options) == 0:
                        return await Message.edit(
                            content=f"  big fuck up happened."
                        )
                    view = discord.ui.View()
                    view.add_item(Select(message.author, message, Options))
                    embed = discord.Embed(
                        color=discord.Color.dark_embed(), title="Modmail Conversation"
                    )
                    embed.set_author(
                        name="Modmail Selection",
                        icon_url="https://cdn.discordapp.com/emojis/1298665792950374410.webp?size=96&quality=lossless",
                    )
                    embed.description = "Select the server you wanna communicate with by pressing the dropdown below."
                    embed.set_footer(
                        icon_url=message.author.display_avatar,
                        text="Your Mutual Servers",
                    )

                    await Message.edit(view=view, embed=embed, content=None)
                except Exception as e:
                    traceback.format_exc(e)
            else:
                Config = await self.client.config.find_one(
                    {"_id": Modmail.get("guild_id")}
                )
                if not Config:
                    return await message.add_reaction("⚠️")
                Guild = await self.client.fetch_guild(Modmail.get("guild_id"))
                if not Guild:
                    return await message.add_reaction("⚠️")
                await Reply(
                    self.client,
                    message=message,
                    Config=Config,
                    ModmailData=Modmail,
                    Guild=Guild,
                )
        if isinstance(message.channel, discord.TextChannel):
            Modmail = await self.client.db["modmail"].find_one(
                {"channel_id": message.channel.id}
            )
            if not Modmail:
                return
            Config = await self.client.config.find_one({"_id": Modmail.get("guild_id")})
            if not Config:
                return
            if not Config.get("Modmail"):
                return
            if not Config.get("Module Options", {}).get("automessage"):
                return
            try:
                User = await message.guild.fetch_member(int(Modmail.get("user_id")))
            except (discord.Forbidden, discord.NotFound):
                return await message.reply(
                    content=f"  I can't find the user they must of left. Probably should delete this."
                )

            if not User:
                return await message.reply(
                    content=f"  I can't find the user they must of left. Probably should delete this."
                )
            embed = discord.Embed(
                color=discord.Color.dark_embed(),
                title=f"**(Staff)** {message.author}",
                description=f"```{message.content}```",
            )
            files = None
            if message.attachments:
                files = [await file.to_file() for file in message.attachments]
            Server = message.guild
            embed.set_author(name=Server.name, icon_url=Server.icon)
            embed.set_thumbnail(url=Server.icon)
            if Config.get("Module Options", {}):
                if Config.get("Module Options").get("MessageFormatting") == "Messages":
                    await message.channel.send(
                        f"<:messagereceived:1201999712593383444> **(Staff)** {message.author.name}: {message.content}"
                    )
                    await User.send(
                        f"<:messagereceived:1201999712593383444> **(Staff)** {message.author.name}: {message.content}"
                    )
                    return await message.delete()

            try:
                await User.send(embed=embed, files=files)
                await message.channel.send(embed=embed, files=files)
                await message.delete()
            except:
                return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ModmailEvent(client))
