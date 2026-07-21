import os

import discord


class Emojis:
    access_control = ""
    add = ""
    alert = ""
    warning = ""
    application = ""
    approval = ""
    dropdown = ""
    arrow_alt = ""
    arrow = ""
    loading_alt = ""
    author = ""
    auto = ""
    auto_response = ""
    bin = ""
    button = ""
    case_warning = ""
    category = ""
    green_tick = ""
    chevron_left = ""
    chevron_right = ""
    chevrons_left = ""
    chevrons_right = ""
    close = ""
    command = ""
    cooldown = ""
    counting = ""
    crisis = ""
    customisation = ""
    red_x = ""
    description = ""
    destroy = ""
    document = ""
    downvote = ""
    edit = ""
    escalate = ""
    exterminate = ""
    flag = ""
    folder = ""
    forum = ""
    globe = ""
    grid_icon = ""
    hammer = ""
    help = ""
    hierarchy = ""
    image = ""
    image_alt = ""
    infractions = ""
    info = ""
    integrations = ""
    join = ""
    leaf = ""
    link = ""
    list = ""
    loa = ""
    loading = ""
    log = ""
    member = ""
    message_icon = ""
    message_forward = ""
    message_quota = ""
    message_received = ""
    modules = ""
    multi_panel = ""
    options = ""
    panel = ""
    partnerships = ""
    pen = ""
    pending = ""
    permissions = ""
    ping = ""
    pin = ""
    premium = ""
    promotions = ""
    qotd = ""
    reason = ""
    red_cross = ""
    replybottom = ""
    replymiddle = ""
    replytop = ""
    reports = ""
    reset = ""
    reviews = ""
    roblox = ""
    role = ""
    role_quota = ""
    save = ""
    settings = ""
    settings_page = ""
    settings_gear = ""
    small_arrow = ""
    sparkle = ""
    staff = ""
    staff_db = ""
    staff_feedback = ""
    staff_list = ""
    star = ""
    start = ""
    static_load = ""
    status_green = ""
    status_red = ""
    stop = ""
    subscription = ""
    suggestion = ""
    suspensions = ""
    system = ""
    progress_bolt = ""
    tags = ""
    threads = ""
    tickets = ""
    time = ""
    tip = ""
    sort_amount = ""
    unlock = ""
    upvote = ""
    utility = ""
    webhook = ""
    website = ""
    tick = ""
    no = ""
    x21 = ""


async def upload(bot: discord.Client, name: str, path: str):
    with open(path, "rb") as f:
        image = f.read()
    return await bot.create_application_emoji(name=name, image=image)


async def load(bot: discord.Client):
    emojis = await bot.fetch_application_emojis()
    for e in emojis:
        if hasattr(Emojis, e.name):
            setattr(Emojis, e.name, str(e))


async def uploadAll(bot: discord.Client, folder: str = "emojis"):
    existing = await bot.fetch_application_emojis()
    existing_names = {e.name for e in existing}

    for filename in os.listdir(folder):
        name, ext = os.path.splitext(filename)
        if ext.lower() not in (".png", ".gif", ".jpg", ".jpeg"):
            continue

        if name in existing_names:
            print(f"skipping {name}, already uploaded")
            continue

        try:
            await upload(bot, name, os.path.join(folder, filename))
            print(f"uploaded {name}")
        except discord.HTTPException as e:
            print(f"failed {name}: {e}")