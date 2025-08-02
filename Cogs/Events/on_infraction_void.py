import discord
from discord.ext import commands
from bson import ObjectId


class on_infraction_void(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_infraction_void(self, _id: ObjectId):
        inf = await self.client.db["infractions"].find_one({"_id": _id})
        if not inf:
            return

        try:
            guild = await self.client.fetch_guild(inf.get("guild_id"))
        except (discord.NotFound, discord.HTTPException, discord.NotFound):
            return
        try:
            staff = await guild.fetch_member(int(inf.get("staff")))
        except (discord.NotFound, discord.HTTPException, discord.NotFound):
            return
        channel = None
        MsgID = None
        Jump = inf.get("jump_url")
        if Jump:
            try:
                ChannelID = int(Jump.split("/")[-2])
                MsgID = int(Jump.split("/")[-1])
                channel = await self.client.fetch_channel(ChannelID)
            except (discord.NotFound, discord.HTTPException, ValueError):
                channel = None
        else:
            channel = None

        if inf.get("Updated"):
            Up = inf["Updated"]
            AddedRoles = Up.get("AddedRoles", [])
            RemovedRoles = Up.get("RemovedRoles", [])
            DbRemoval = Up.get("DbRemoval")

            Add = [role for R in AddedRoles if (role := guild.get_role(R))]
            Remove = [role for R in RemovedRoles if (role := guild.get_role(R))]

            if Add:
                try:
                    await staff.remove_roles(*Add)
                except:
                    pass

            if Remove:
                try:
                    await staff.add_roles(*Remove)
                except:
                    pass

            if DbRemoval:
                try:
                    await self.client.db["staff database"].insert_one(DbRemoval)
                except:
                    pass
        if channel:
            try:

                if inf.get("WebhookID"):
                    Msg = await self.client.fetch_webhook(inf.get("WebhookID"))

                else:
                    Msg = await channel.fetch_message(MsgID)
            except (discord.NotFound, discord.HTTPException):
                return
            if not channel:
                return
            E = Msg.embeds
            E2 = discord.Embed(
                color=discord.Color.orange(),
            ).set_author(
                name="Infraction Voided",
                icon_url="https://cdn.discordapp.com/emojis/1345821183328784506.webp?size=96",
            )
            try:
                await Msg.edit(embeds=E + [E2])
            except (discord.NotFound, discord.Forbidden):
                return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_infraction_void(client))
