import discord
from sentry_sdk import metrics

class Support(discord.ui.View):
    def __init__(self):
        super().__init__()
        url1 = "https://discord.gg/DhWdgfh3hN"
        self.add_item(
            discord.ui.Button(
                label="Support Server",
                url=url1,
                style=discord.ButtonStyle.blurple,
                emoji="<:link:1206670134064717904>",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Documentation",
                url="https://docs.astrobirb.dev",
                style=discord.ButtonStyle.blurple,
                emoji="📚",
            )
        )


def NotRobloxLinked():
    return discord.Embed(
        description="```\nYour Roblox account is not linked.\n```",
        color=discord.Color.brand_red(),
    ).add_field(
        name="<:Help:1184535847513624586> How To Fix",
        value="> 1. Use the `/integrations link` command to link your Roblox account.",
    )


def ChannelNotFound():
    return discord.Embed(
        description="```\nI couldn't find the channel for this.\n```",
        color=discord.Color.brand_red(),
    ).add_field(
        name="<:Help:1184535847513624586> How To Fix",
        value="> 1. Head to </config:1140463441136586784> and make sure to go to the module and set the channel.\n> 2. Ensure I have permission to access that channel (`View Channel, Read Messages, Send Messages`).",
    )


def CustomError(error: str):
    return discord.Embed(
        description=f"```\n{error}\n```", color=discord.Color.brand_red()
    )


def NoPermissionChannel(channel: discord.TextChannel):
    return discord.Embed(
        description=f"```\nI don't have permission to send messages in <#{channel.id}>.\n```",
        color=discord.Color.brand_red(),
    ).add_field(
        name="<:Help:1184535847513624586> How To Fix",
        value="> 1. Ensure I have permission to send messages in that channel.\n> 2. Check that I have the required permissions (`View Channel, Read Messages, Send Messages`).",
    )


def NoPremium():
    metrics.count("Popup:Premium", 1)
    return discord.Embed(
        description="```\nThis feature is only available for premium servers.\n```",
        color=discord.Color.blurple(),
    ).add_field(
        name="<:Premium:1250160559203287080> Premium",
        value="> If you already have premium go to /config → Subscriptions and activate your server.\n-# If you have premium and your subscription isn't showing up run /patreon.",
    )

def NotYourPanel():
    return discord.Embed(
        description="```\nThis is not your panel.\n```",
        color=discord.Color.brand_red(),
    )

def GlobalMaintenance(reason: str):
    return discord.Embed(
        description=f"```\nBirb is currently undergoing maintenance.\n```",
        color=discord.Color.brand_red(),
    ).add_field(
        name="Reason",
        value=f"> {reason}"
    )

def NoChannelSet():
    return discord.Embed(
        description="```\nNo channel has been set for this module.\n```",
        color=discord.Color.brand_red(),
    ).add_field(
        name="<:Help:1184535847513624586> How To Fix",
        value="> 1. Head to </config:1140463441136586784> and make sure to go to the module and set the channel.",
    )


def ModuleNotEnabled():
    return discord.Embed(
        description="```\nThis module hasn't been enabled yet.\n```",
        color=discord.Color.brand_red(),
    ).add_field(
        name="<:Help:1184535847513624586> How To Fix",
        value="> 1. Head to </config:1140463441136586784> and go to the Modules section to find the module.\n> 2. Select the module, and then go back to the config menu.\n> 3. You should be able to see it, and now you can configure it to suit your needs.",
    )


def BotNotConfigured():
    return discord.Embed(
        description="```\nI haven't been configured yet.\n```",
        color=discord.Color.brand_red(),
    ).add_field(
        name="<:Help:1184535847513624586> How To Fix",
        value="> 1. Run the `/config` command to configure me.",
    )


def ModuleNotSetup():
    return discord.Embed(
        description="```\nThis module hasn't been set up yet.\n```",
        color=discord.Color.brand_red(),
    ).add_field(
        name="<:Help:1184535847513624586> How To Fix",
        value="> 1. Run the `/config` command to set up the module.",
    )
