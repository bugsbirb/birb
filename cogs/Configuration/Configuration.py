import logging

from discord.ext import commands

from core.bot.HelpEmbeds import NoPremium, Support, NotYourPanel
from core.bot.emojis import *
from core.bot.permissions import premium
from core.bot.ui import PMButton

logger = logging.getLogger(__name__)


async def Reset(i: discord.Interaction, *F):
    try:
        view = discord.ui.View()
        for E in F:
            view.add_item(E())
        await i.edit_original_response(view=view)
    except:
        pass


class ConfigMenu(discord.ui.Select):
    def __init__(self, options: list, author: discord.Member) -> None:
        self.author = author
        super().__init__(placeholder="Config Menu", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)

        from cogs.Configuration.Components.Modules import ModuleToggle, ModuleOptions

        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {
                "_id": interaction.guild.id,
                "Modules": {},
                "Infractions": {},
                "Permissions": {},
            }
        view = discord.ui.View()

        selection = self.values[0]
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        embed = discord.Embed(color=discord.Colour.dark_embed())

        await Reset(interaction, lambda: ConfigMenu(Options(Config), interaction.user))

        if selection == "Permissions":
            from cogs.Configuration.Components.Permissions import (
                PermissionsEmbed,
                PermissionsUpdate,
            )
            from cogs.Configuration.Components.AdvancedPermissions import (
                PermissionsDropdown,
            )

            embed = await PermissionsEmbed(interaction, Config, embed)
            view.add_item(
                PermissionsUpdate(
                    interaction.user,
                    "staffrole",
                    [
                        role
                        for role in interaction.guild.roles
                        if role.id in Config.get("Permissions", {}).get("staffrole", [])
                        or None
                    ],
                )
            )
            view.add_item(
                PermissionsUpdate(
                    interaction.user,
                    "adminrole",
                    [
                        role
                        for role in interaction.guild.roles
                        if role.id in Config.get("Permissions", {}).get("adminrole", [])
                        or None
                    ],
                )
            )
            view.add_item(PermissionsDropdown(interaction.user))
        elif selection == "Edit Profile":
            from cogs.Configuration.Components.WLite import WLiteOption, WLiteEmbed

            embed = await WLiteEmbed(interaction)
            view = discord.ui.View()
            view.add_item(WLiteOption(interaction.user))

        elif selection == "Modules":
            embed.set_author(
                name=f"{interaction.guild.name}", icon_url=interaction.guild.icon
            )
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.description = "> This is where you can toggle your server's modules! If you wanna know more about what these modules do head to the [documentation](https:/docs.astrobirb.dev)"

            view.add_item(
                ModuleToggle(
                    interaction.user,
                    await ModuleOptions(Config),
                )
            )
        elif selection == "Hierarchy":
            from cogs.Configuration.Components.Hirearchys import HSELECT, HiEmbed

            embed = await HiEmbed(interaction, Config, embed)
            view = discord.ui.View()
            view.add_item(
                HSELECT(
                    interaction.user,
                    Config.get("Promo", {}).get("System", {}).get("type", "og"),
                )
            )
        elif selection == "infractions":
            from cogs.Configuration.Components.Infractions import (
                InfractionEmbed,
                InfractionOption,
            )

            embed = await InfractionEmbed(interaction, Config, embed)
            view = discord.ui.View()
            view.add_item(
                InfractionOption(
                    interaction.user,
                )
            )
        elif selection == "promotions":
            from cogs.Configuration.Components.Promotions import (
                PromotionEmbed,
                PSelect,
            )

            embed = await PromotionEmbed(interaction, Config, embed)
            view = discord.ui.View()
            view.add_item(
                PSelect(
                    interaction.user,
                )
            )
        elif selection == "Modmail":
            from cogs.Configuration.Components.Modmail import (
                ModmailEmbed,
                ModmailOptions,
            )

            embed = await ModmailEmbed(interaction, Config, embed)
            view = discord.ui.View()
            view.add_item(
                ModmailOptions(
                    interaction.user,
                    Config.get("Module Options", {}).get("ModmailType", "channel"),
                )
            )
        elif selection == "Feedback":
            from cogs.Configuration.Components.StaffFeedback import (
                StaffFeedbackEmbed,
                StaffFeedback,
            )

            embed = await StaffFeedbackEmbed(interaction, Config, embed)
            view = discord.ui.View()
            view.add_item(
                StaffFeedback(
                    interaction.user,
                )
            )
        elif selection == "Quota":
            from cogs.Configuration.Components.MessageQuota import (
                MessageQuotaEmbed,
                QuotaOptions,
            )

            embed = await MessageQuotaEmbed(interaction, Config, embed)
            view = discord.ui.View()
            view.add_item(
                QuotaOptions(
                    interaction.user,
                )
            )
        elif selection == "LOA":
            from cogs.Configuration.Components.LOA import (
                LOAEmbed,
                LOAOptions,
            )

            embed = await LOAEmbed(interaction, Config, embed)
            view = discord.ui.View()
            view.add_item(
                LOAOptions(
                    interaction.user,
                )
            )
        elif selection == "suggestions":
            from cogs.Configuration.Components.Suggestions import (
                SuggestionsEmbed,
                Suggestions,
            )

            embed = await SuggestionsEmbed(interaction, Config, embed)
            view = discord.ui.View()
            view.add_item(
                Suggestions(
                    interaction.user,
                )
            )
        elif selection == "Staff Database":
            from cogs.Configuration.Components.StaffPanel import (
                StaffPanelEmbed,
                StaffPanelOptions,
            )

            embed = await StaffPanelEmbed(interaction, embed)
            view = discord.ui.View()
            view.add_item(
                StaffPanelOptions(
                    interaction.user,
                )
            )
        elif selection == "customcommands":
            try:
                from cogs.Configuration.Components.CustomCommands import (
                    CustomCommandsEmbed,
                    CustomCommands,
                )

                view = discord.ui.View()
                embed = await CustomCommandsEmbed(interaction, embed)
                view.add_item(
                    CustomCommands(
                        interaction.user,
                    )
                )
            except Exception as e:
                import traceback

                logger.error(traceback.format_exc(e))
        elif selection == "Forums":
            from cogs.Configuration.Components.Forums import ForumsOptions, ForumsEmbed

            embed = await ForumsEmbed(interaction, embed)

            view = discord.ui.View()
            view.add_item(ForumsOptions(interaction.user))
        elif selection == "suspensions":
            from cogs.Configuration.Components.Suspensions import (
                SuspensionEmbed,
                SuspensionOptions,
            )

            embed = await SuspensionEmbed(interaction, Config, embed)
            view = discord.ui.View()
            view.add_item(SuspensionOptions(interaction.user))
        elif selection == "QOTD":
            from cogs.Configuration.Components.QOTD import (
                QOTDEMbed,
                QOTDOptions,
            )

            daily = await interaction.client.db["qotd"].find_one(
                {"guild_id": interaction.guild.id}
            )

            if daily and daily.get("nextdate", None):
                options = [
                    discord.SelectOption(
                        label="Stop QOTD",
                        emoji=f"{Emojis.stop}",
                        description="End the daily questions.",
                    ),
                    discord.SelectOption(label="Channel", emoji=f"{Emojis.tags}"),
                    discord.SelectOption(
                        label="Webhook",
                        description="Premium Required. Send it as a webhook.",
                        emoji=f"{Emojis.webhook}",
                    ),
                    discord.SelectOption(label="Ping", emoji=f"{Emojis.ping}"),
                    discord.SelectOption(
                        label="Custom Questions",
                        emoji=f"{Emojis.message_icon}",
                        description="Premium Required.",
                    ),
                    discord.SelectOption(label="Preferences", emoji=f"{Emojis.leaf}"),
                ]
            else:
                options = [
                    discord.SelectOption(
                        label="Start QOTD",
                        emoji=f"{Emojis.start}",
                        description="Start the daily questions. (Pressing this while its already started will restart it.)",
                    ),
                    discord.SelectOption(label="Channel", emoji=f"{Emojis.tags}"),
                    discord.SelectOption(
                        label="Webhook",
                        description="Premium Required. Send it as a webhook. ",
                        emoji=f"{Emojis.webhook}",
                    ),
                    discord.SelectOption(label="Ping", emoji=f"{Emojis.ping}"),
                    discord.SelectOption(
                        label="Custom Questions",
                        emoji=f"{Emojis.message_icon}",
                        description="Premium Required.",
                    ),
                    discord.SelectOption(label="Preferences", emoji=f"{Emojis.leaf}"),
                ]

            embed = await QOTDEMbed(interaction, embed)
            view = discord.ui.View()
            view.add_item(QOTDOptions(interaction.user, options))
        elif selection == "Subscriptions":
            from cogs.Configuration.Components.Subscriptions import (
                SubscriptionsEmbed,
                PremiumButtons,
            )

            result = await interaction.client.db["Subscriptions"].find_one(
                {"guilds": {"$in": [interaction.guild.id]}}
            )
            view = discord.ui.View()
            user = await interaction.client.db["Subscriptions"].find_one(
                {"user": interaction.user.id}
            )
            if not user and not result:
                view = PMButton()
            if user and not result:
                view = PremiumButtons(interaction.user)
                view.disable.disabled = True
            if user and result:
                view = PremiumButtons(interaction.user)
                view.disable.disabled = False
                view.enable.disabled = True
            embed = await SubscriptionsEmbed(interaction)
        elif selection == "Auto Responder":
            if not await premium(interaction.guild.id):
                return await interaction.followup.send(
                    embed=NoPremium(), view=Support()
                )

            from cogs.Configuration.Components.AutoResponse import (
                AutoResponseEmbed,
                AutoResponderOptions,
            )

            embed = await AutoResponseEmbed(interaction, embed)
            view = discord.ui.View()
            view.add_item(
                AutoResponderOptions(
                    interaction.user,
                )
            )
        elif selection == "Integrations":
            from cogs.Configuration.Components.integrations import (
                integrationsEmbed,
                Integrations,
            )

            view = discord.ui.View()
            view.add_item(Integrations(interaction.user))
            embed = await integrationsEmbed(interaction, embed=embed)
        elif selection == "Tickets":
            from cogs.Configuration.Components.Tickets import TicketsEmbed, Tickets

            view = discord.ui.View()
            view.add_item(Tickets(interaction.user))
            embed = await TicketsEmbed(interaction, embed=embed)
        elif selection == "Staff List":
            from cogs.Configuration.Components.stafflist import StaffListEmbed

            view = discord.ui.View()
            embed = await StaffListEmbed(interaction, embed=embed)
        view.add_item(ConfigMenu(Options(Config), interaction.user))
        await interaction.edit_original_response(embed=embed, view=view)


def DefaultEmbed(guild: discord.Guild):
    embed = discord.Embed(
        title="Configuration",
        description=f"{Emojis.options} Select **an option** to manage your server's configuration.",
        color=discord.Color.dark_embed(),
    )
    embed.add_field(
        name=f"{Emojis.partnerships} Support Server",
        value="> If you ever have issues with the bot or require assistance come and talk to someone in [#get-support](https://discord.gg/23TD4vQXJA).",
        inline=False,
    )
    embed.add_field(
        name=f"{Emojis.help} Documentation",
        value="> The best way to learn how to use **Birb** is through the [**documentation**](https://astrobirb.dev)!",
        inline=False,
    )
    embed.set_thumbnail(url=guild.icon)
    embed.set_author(name=guild.name, icon_url=guild.icon)
    return embed


def Options(Config: dict = None):
    if not Config:
        Config = {"Modules": {}}
    Modules = Config.get("Modules", {})
    options = [
        discord.SelectOption(
            label="Permissions",
            description="Manage your server's permissions.",
            emoji=f"{Emojis.settings_page}",
        ),
        discord.SelectOption(
            label="Modules",
            description="Manage your server's modules",
            emoji=f"{Emojis.modules}",
        ),
        discord.SelectOption(
            label="Edit Profile",
            description="Edit the bots avatar & nickname.",
            emoji=f"{Emojis.pen}",
        ),
        discord.SelectOption(
            label="Subscriptions",
            description="Manage your server's subscriptions",
            emoji=f"{Emojis.subscription}",
        ),
        discord.SelectOption(
            label="Integrations",
            description="Use External APIs.",
            emoji=f"{Emojis.link}",
        ),
        discord.SelectOption(
            label="Hierarchy",
            description="Hierarchies for both promotions & infractions.",
            emoji=f"{Emojis.hierarchy}",
        ),
    ]

    ModuleAddons = [
        discord.SelectOption(
            label="Infractions",
            description="",
            emoji=f"{Emojis.infractions}",
            value="infractions",
        ),
        discord.SelectOption(
            label="Promotions",
            description="",
            emoji=f"{Emojis.promotions}",
            value="promotions",
        ),
        discord.SelectOption(
            label="Message Quota",
            description="",
            value="Quota",
            emoji=f"{Emojis.message_quota}",
        ),
        discord.SelectOption(
            label="Leave Of Absence",
            description="",
            value="LOA",
            emoji=f"{Emojis.loa}",
        ),
        discord.SelectOption(
            label="Tickets",
            value="Tickets",
            emoji=f"{Emojis.tickets}",
            description="",
        ),
        discord.SelectOption(
            label="Modmail",
            description="",
            value="Modmail",
            emoji=f"{Emojis.message_received}",
        ),
        discord.SelectOption(
            label="Custom Commands",
            description="",
            value="customcommands",
            emoji=f"{Emojis.command}",
        ),
        discord.SelectOption(
            label="Staff List",
            description="",
            value="Staff List",
            emoji=f"{Emojis.staff_list}",
        ),
        discord.SelectOption(
            label="Forums",
            description="",
            value="Forums",
            emoji=f"{Emojis.forum}",
        ),
        discord.SelectOption(
            label="Suspensions",
            description="",
            value="suspensions",
            emoji=f"{Emojis.suspensions}",
        ),
        discord.SelectOption(
            label="Daily Questions",
            emoji=f"{Emojis.qotd}",
            description="",
            value="QOTD",
        ),
        discord.SelectOption(
            label="Suggestions",
            description="",
            value="suggestions",
            emoji=f"{Emojis.suggestion}",
        ),
        discord.SelectOption(
            label="Staff Feedback",
            description="",
            value="Feedback",
            emoji=f"{Emojis.staff_feedback}",
        ),
        discord.SelectOption(
            label="Staff Panel",
            description="",
            value="Staff Database",
            emoji=f"{Emojis.staff_db}",
        ),
        discord.SelectOption(
            label="Auto Response",
            value="Auto Responder",
            emoji=f"{Emojis.auto_response}",
        ),
    ]

    for module in ModuleAddons:
        if Modules.get(module.value, False):
            options.append(module)

    return options


class ConfigCog(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @commands.hybrid_command(description="Configure the bot for your servers needs")
    @commands.has_guild_permissions(manage_guild=True)
    async def config(self, ctx: commands.Context):
        Config = await self.client.db["Config"].find_one({"_id": ctx.guild.id})
        if (
            not Config
            or "Infraction" not in Config
            or not Config["Infraction"].get("types")
        ):
            if not Config:
                Config = {
                    "_id": ctx.guild.id,
                    "Modules": {},
                    "Infraction": {"types": []},
                }
            if not Config.get("Infraction"):
                Config["Infraction"] = {}
            Config["Infraction"]["types"] = [
                "Activity Notice",
                "Verbal Warning",
                "Warning",
                "Strike",
                "Demotion",
                "Termination",
            ]
            await self.client.config.update_one(
                {"_id": ctx.guild.id}, {"$set": Config}, upsert=True
            )

        options = Options(Config)
        view = discord.ui.View()
        view.add_item(ConfigMenu(options, ctx.author))

        embed = DefaultEmbed(ctx.guild)
        await ctx.send(embed=embed, view=view)

    @config.error
    async def PermsHandler(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                f"{Emojis.no} **{ctx.author.display_name},** you are missing the `Manage Server` permission."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ConfigCog(client))
