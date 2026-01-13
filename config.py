# ==============================
# CONFESSION CONFIGURATION
# ==============================
GUILD_ID = 1454926746783584328 # Replace with your server ID
# ==============================
# MODERATION
# ==============================

ADMIN_ROLE_IDS = [
    1456089045166854226  # <-- replace with your admin/mod role IDs
]
CONFESSION_LOG_FORMAT = (
    "🧾 **Confession #{id}**\n"
    "👤 Author: {user_id}\n"
    "📨 Message ID: {message_id}\n"
    "🔎 Looking for: {role}\n"
    "🕒 Time: {time}"
)

# Channels
CONFESSION_CHANNEL_ID = 1456153374633234546
MOD_LOG_CHANNEL_ID = 1456778417247621151

# Dating roles (supports LGBTQ+)
# Key = display name for dropdown / embed
# Value = Discord role ID
ROLE_MAPPING = {
    "He/Him": 1456059354607255612,
    "She/Her": 1456059535612444712,
    "They/Them": 1456059540943409277,
    # Add new roles here
}

# Auto-generated for dropdown
ROLE_SELECT_OPTIONS = list(ROLE_MAPPING.keys())

# Default anonymous thumbnail
BLUR_THUMBNAIL = "https://i.imgur.com/blur.png"

# Embed template
CONFESSION_EMBED = {
    "Author": "#{id}",
    "title": "🔎 Looking for: {looking_role_mention}",  # We will insert role mention here
    "description": "{message}",
    "color": 0xf33870,
    "footer": "Anonymous",
    "thumbnail": BLUR_THUMBNAIL
}

# Rules & Protection
CONFESSION_RULES = {
    "max_length": 500,
    "block_mentions": True,
    "delete_command": True,
    "cooldown_seconds": 60
}

# Button Labels
CONFESSION_BUTTONS = {
    "reply": "Reply",
    "post": "Post",
    "dm": "DM"
}
