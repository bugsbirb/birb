import discord
from discord.ext import commands
from emojis import *
import os
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
blacklists = db['blacklists']

class webGuildJoins(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        blacklist = await blacklists.find_one({'user': guild.owner.id})
        if blacklist:
            return
        channel_id = 1178362100737916988 
        channel = self.client.get_channel(channel_id)

        if channel:
            webhook = discord.utils.get(await channel.webhooks(), name="Public Bot Logs")
            try:
             await webhook.send(f"<:join:1140670830792159373> I am now in {len(self.client.guilds)} guilds.", username=guild.name, avatar_url=guild.icon)
            except discord.HTTPException:
                print('[ERROR] Can\'t send guild join message its too long.')
                pass 
            inviter = None
            async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add):
                if entry.target.id == self.client.user.id:
                    inviter = entry.user
                    break
            if inviter:
                try:
                    await inviter.send(f"🎉 Thank you for adding **Astro Birb** to your server. To get started run </config:1140463441136586784>!\n<:ArrowDropDown:1163171628050563153> Guild `#{len(self.client.guilds)}`")
                except discord.Forbidden:
                    print("[⚠️] I couldn't DM the owner of the guild for the guild join.")
class Support(discord.ui.View):
    def __init__(self):
        super().__init__()
        url1 = 'https://discord.gg/DhWdgfh3hN'
        self.add_item(discord.ui.Button(label='Support Server', url=url1, style=discord.ButtonStyle.blurple, emoji="<:link:1206670134064717904>"))
        self.add_item(discord.ui.Button(label='Documentation', url="https://docs.astrobirb.dev/overview", style=discord.ButtonStyle.blurple, emoji="📚"))



async def setup(client: commands.Bot) -> None:
    await client.add_cog(webGuildJoins(client))   