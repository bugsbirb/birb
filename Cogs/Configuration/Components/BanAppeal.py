import discord
import discord.http
from utils.emojis import *

from dotenv import load_dotenv
from discord.ui import Modal, TextInput

load_dotenv()
# Mongos = AsyncIOMotorClient(os.getenv("MONGO_URL"))
# DB = Mongos["astro"]
# Customisation = DB["Customisation"]
# interaction.client.db["Ban Appeals Configuration"] = DB["Ban Appeals Configuration"]


class BanAppealOptions(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Manage Questions", emoji="<:Application:1224722901328986183>"
                ),
                discord.SelectOption(
                    label="Channel", emoji="<:tag:1234998802948034721>"
                ),
            ]
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
        option = interaction.data["values"][0]
        if option == "Manage Questions":
            result = await interaction.client.db["Ban Appeals Configuration"].find_one({"guild_id": interaction.guild.id})
            if result and "questions" in result:
                questions = result["questions"]
                description = ""

                for key, question in sorted(
                    questions.items(), key=lambda x: int(x[0].replace("question", ""))
                ):
                    KEy = int(key.replace("question", ""))
                    description += f"> **Question {KEy}:** {question}\n"

            else:
                description = "No questions found."

            embed = discord.Embed(
                title="",
                description=description,
                color=discord.Colour.dark_embed(),
            )
            embed.set_author(
                name="Manage Questions",
                icon_url="https://cdn.discordapp.com/emojis/1178754449125167254.webp?size=96&quality=lossless",
            )
            embed.set_thumbnail(url=interaction.guild.icon)
            view = ManageQuestions(self.author)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        elif option == "Channel":
            result = await interaction.client.db["Ban Appeals Configuration"].find_one({"guild_id": interaction.guild.id})
            view = discord.ui.View()
            view.add_item(
                AppealSubChannel(
                    self.author,
                    interaction.message,
                )
            )
            await interaction.followup.send(view=view, ephemeral=True)


class ManageQuestions(discord.ui.View):
    def __init__(self, author):
        self.author = author
        super().__init__(timeout=360)

    @discord.ui.button(
        label="",
        emoji="<:Add:1163095623600447558>",
        style=discord.ButtonStyle.grey,
        row=0,
    )
    async def add_question(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        await interaction.response.send_modal(CreateQuestionModal(interaction.user))

    @discord.ui.button(
        emoji="<:Subtract:1229040262161109003>", style=discord.ButtonStyle.grey, row=0
    )
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        await interaction.response.send_modal(DeleteQuestionModal(interaction.user))


class CreateQuestionModal(Modal):
    def __init__(self, author):
        super().__init__(title="Create Question")
        self.author = author
        self.question = TextInput(
            label="Question",
            placeholder="Enter the question",
            style=discord.TextStyle.short,
        )
        self.add_item(self.question)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        question = self.question.value

        result = await interaction.client.db["Ban Appeals Configuration"].find_one({"guild_id": interaction.guild.id})
        if result and "questions" in result:
            questions = result["questions"]
            numeric_index = max(
                (
                    int(k.replace("question", ""))
                    for k in questions.keys()
                    if k.startswith("question")
                ),
                default=0,
            )
            next_index = numeric_index + 1

            questions[f"question{next_index}"] = question

            await interaction.client.db["Ban Appeals Configuration"].update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {"questions": questions}},
                upsert=True,
            )
        else:
            data = {"guild_id": interaction.guild.id}
            await interaction.client.db["Ban Appeals Configuration"].update_one(
                data, {"$set": {"questions": {"question1": question}}}, upsert=True
            )

        result = await interaction.client.db["Ban Appeals Configuration"].find_one({"guild_id": interaction.guild.id})
        if result and "questions" in result:
            questions = result["questions"]
            description = ""

            for key, question_text in sorted(
                questions.items(), key=lambda x: int(x[0].replace("question", ""))
            ):
                key_number = int(key.replace("question", ""))
                description += f"> **Question {key_number}:** {question_text}\n"

        else:
            description = "No questions found."

        embed = discord.Embed(
            description=description,
            color=discord.Colour.dark_embed(),
        )
        embed.set_author(
            name="Manage Questions",
            icon_url="https://cdn.discordapp.com/emojis/1178754449125167254.webp?size=96&quality=lossless",
        )
        embed.set_thumbnail(url=interaction.guild.icon)
        await interaction.response.edit_message(embed=embed)


class DeleteQuestionModal(Modal):
    def __init__(self, author):
        super().__init__(title="Delete")
        self.author = author
        self.question = TextInput(
            label="Question",
            placeholder="Enter the question",
            style=discord.TextStyle.short,
        )
        self.add_item(self.question)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        result = await interaction.client.db["Ban Appeals Configuration"].find_one({"guild_id": guild_id})

        if not result:
            return await interaction.response.send_message(
                "No questions found for this guild.", ephemeral=True
            )

        questions = result.get("questions", {})

        if self.question.value not in questions.values():
            return await interaction.response.send_message(
                f"  Question not found.", ephemeral=True
            )

        questions = result["questions"]
        question = self.question.value
        question_id_to_delete = None
        for key, value in questions.items():
            if value == question:
                question_id_to_delete = key
                break

        if question_id_to_delete:
            del questions[question_id_to_delete]

        await interaction.client.db["Ban Appeals Configuration"].update_one(
            {"guild_id": guild_id}, {"$set": {"questions": questions}}, upsert=True
        )
        result = await interaction.client.db["Ban Appeals Configuration"].find_one({"guild_id": interaction.guild.id})
        if result and "questions" in result:
            questions = result.get("questions", {})
            description = ""

            for key, question_text in questions.items():
                key = int(key.replace("question", ""))
                description += f"> **Question {key}:** {question_text}\n"

        else:
            description = "No questions found."

        embed = discord.Embed(
            description=description,
            color=discord.Colour.dark_embed(),
        )
        embed.set_author(
            name="Manage Questions",
            icon_url="https://cdn.discordapp.com/emojis/1178754449125167254.webp?size=96&quality=lossless",
        )
        embed.set_thumbnail(url=interaction.guild.icon)
        await interaction.response.edit_message(embed=embed)


class AppealSubChannel(discord.ui.ChannelSelect):
    def __init__(self, author: discord.Member,  msg: discord.Message):
        super().__init__(
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        await interaction.client.db["Ban Appeals Configuration"].update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"banchannel": self.values[0].id if self.values else None}},
            upsert=True,
        )
        await self.msg.edit(embed=await BanAppealEmbed(interaction, discord.Embed(color=discord.Color.dark_embed())))


async def BanAppealEmbed(interaction: discord.Interaction, embed: discord.Embed):
    config = await interaction.client.db["Ban Appeals Configuration"].find_one({"guild_id": interaction.guild.id})
    if not config:
        config = {"banchannel": None}
    
    channel = (
        interaction.guild.get_channel(config.get("banchannel", None)) or "Not Configured"
    )

    if isinstance(channel, discord.TextChannel):
        channel = channel.mention

    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> This is your server's Ban Appeal configuration. If the moderation bot you are using doesn't have ban appeal's, you can use this. (Alert: Doesn't work if the user doesn't have mutual servers with the bot.) You can find out more at [the documentation](https://docs.astrobirb.dev/)"
    embed.add_field(
        name="<:settings:1207368347931516928> Appeals",
        value=f"> `Appeal Channel:` {channel}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)",
        inline=False,
    )
    return embed
