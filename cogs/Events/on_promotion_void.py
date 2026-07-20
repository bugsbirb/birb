import discord
from bson import ObjectId
from discord.ext import commands


class on_promotion_void(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_promotion_void(self, _id: ObjectId):
        promotion = await self.client.db["promotions"].find_one({"_id": _id})
        if not promotion:
            return

        try:
            guild = await self.client.fetch_guild(promotion.get("guild_id"))
        except (discord.NotFound, discord.HTTPException):
            return
        try:
            staff = await guild.fetch_member(int(promotion.get("staff")))
        except (discord.NotFound, discord.HTTPException):
            return
        channel = None
        MsgID = None
        Jump = promotion.get("jump_url")
        if Jump:
            try:
                ChannelID = int(Jump.split("/")[-2])
                MsgID = int(Jump.split("/")[-1])
                channel = await self.client.fetch_channel(ChannelID)
            except (discord.NotFound, discord.HTTPException, ValueError):
                channel = None
        else:
            channel = None

        if channel:
            try:
                Msg = await channel.fetch_message(MsgID)
            except (discord.NotFound, discord.HTTPException):
                return
            if not channel:
                return
            E = Msg.embeds[0]
            E2 = discord.Embed(
                color=discord.Color.green(),
            ).set_author(
                name="Promotion Voided",
                icon_url="https://cdn.discordapp.com/emojis/1345821183328784506.webp?size=96",
            )
            try:
                await Msg.edit(embeds=[E, E2])
            except (discord.NotFound, discord.Forbidden):
                return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_promotion_void(client))
