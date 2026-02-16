import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput, Select
from datetime import datetime, timedelta, timezone
import config
from PIL import Image, ImageFilter
import requests, io, os
from dotenv import load_dotenv
import os


# ==============================
# LOAD TOKEN
# ==============================
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN environment variable not set")

# ==============================
# BOT SETUP
# ==============================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# STORAGE
# ==============================
cooldowns = {}
message_counter = 0
message_authors = {}  # message_id -> user_id

# ==============================
# HELPERS
# ==============================
def is_on_cooldown(uid):
    return uid in cooldowns and cooldowns[uid] > datetime.now(timezone.utc)

def set_cooldown(uid):
    cooldowns[uid] = datetime.now(timezone.utc) + timedelta(
        seconds=config.CONFESSION_RULES["cooldown_seconds"]
    )

def get_blurred_avatar(user):
    os.makedirs("avatars", exist_ok=True)
    path = f"avatars/{user.id}.png"
    if not os.path.exists(path):
        r = requests.get(user.display_avatar.url)
        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        img = img.resize((256, 256))
        img = img.filter(ImageFilter.GaussianBlur(18))
        img.save(path)
    return path

# ==============================
# POST MESSAGE MODAL
# ==============================
class PostMessageModal(Modal):
    def __init__(self, role_label):
        super().__init__(title="Anonymous Message")
        self.role_label = role_label
        self.msg = TextInput(
            label="Message",
            style=discord.TextStyle.paragraph,
            max_length=config.CONFESSION_RULES["max_length"]
        )
        self.add_item(self.msg)

    async def on_submit(self, interaction: discord.Interaction):
        global message_counter

        if is_on_cooldown(interaction.user.id):
            await interaction.response.send_message("⏳ Slow down.", ephemeral=True)
            return

        set_cooldown(interaction.user.id)
        message_counter += 1

        role_id = config.ROLE_MAPPING[self.role_label]
        role_mention = f"<@&{role_id}>"

        avatar = get_blurred_avatar(interaction.user)
        file = discord.File(avatar, filename="avatar.png")

        embed = discord.Embed(
            title="Anonymous",
            description=f"{self.msg.value}\n\n🔎 Looking for: {role_mention}",
            color=0xf33870,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_author(name=f"Message #{message_counter}")
        embed.set_footer(text="Anonymous sent")
        embed.set_thumbnail(url="attachment://avatar.png")

        channel = interaction.guild.get_channel(config.CONFESSION_CHANNEL_ID)
        msg = await channel.send(
            embed=embed,
            file=file,
            view=MessageButtons(None)
        )

        message_authors[msg.id] = interaction.user.id
        await msg.edit(view=MessageButtons(msg.id))

        await interaction.response.send_message("✅ Message posted.", ephemeral=True)

# ==============================
# REPLY MODAL
# ==============================
class ReplyModal(Modal):
    def __init__(self, mid):
        super().__init__(title="Anonymous Reply")
        self.mid = mid
        self.reply = TextInput(label="Reply", style=discord.TextStyle.paragraph)
        self.add_item(self.reply)

    async def on_submit(self, interaction):
        embed = discord.Embed(
            title="💬 Anonymous Reply",
            description=self.reply.value,
            color=discord.Color.blurple()
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Reply sent.", ephemeral=True)

# ==============================
# DM REQUEST MODAL (replier types message)
# ==============================
class DMMessageModal(Modal):
    def __init__(self, poster: discord.User):
        super().__init__(title="Send DM Request")
        self.poster = poster
        self.msg_input = TextInput(
            label="Your message",
            style=discord.TextStyle.paragraph,
            max_length=300
        )
        self.add_item(self.msg_input)

    async def on_submit(self, interaction: discord.Interaction):
        replier = interaction.user

        # Safely fetch member to get roles
        member = interaction.guild.get_member(replier.id)
        if member is None:
            try:
                member = await interaction.guild.fetch_member(replier.id)
            except:
                member = None

        if member:
            roles = [r.mention for r in member.roles if r.name != "@everyone"]
            replier_status = " ".join(roles) if roles else "No roles"
        else:
            replier_status = "No roles"

        embed = discord.Embed(
            title="📩 DM Request",
            description=f"{replier.mention} wants to send you a DM.\n\n**Status:**\n{replier_status}",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )

        await self.poster.send(
            embed=embed,
            view=DMRequestView(self.poster, replier, replier_status, self.msg_input.value)
        )

        await interaction.response.send_message(
            "⏳ DM request sent to the poster. Waiting for approval…",
            ephemeral=True
        )

# ==============================
# DM REQUEST APPROVAL VIEW
# ==============================
class DMRequestView(View):
    def __init__(self, poster: discord.User, replier: discord.User, replier_status: str, msg_content: str):
        super().__init__(timeout=300)  # 5 min to respond
        self.poster = poster
        self.replier = replier
        self.replier_status = replier_status
        self.msg_content = msg_content

    @discord.ui.button(label="Accept DM", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.poster.id:
            await interaction.response.send_message("❌ You are not allowed to make this decision.", ephemeral=True)
            return

        try:
            await self.replier.send(embed=discord.Embed(
                title="📩 Anonymous DM",
                description=self.msg_content,
                color=discord.Color.green()
            ))
            await interaction.response.edit_message(
                content="✅ You accepted the DM request.",
                embed=None,
                view=None
            )
        except:
            await interaction.response.edit_message(
                content="❌ Failed to send DM.",
                embed=None,
                view=None
            )

    @discord.ui.button(label="Refuse DM", style=discord.ButtonStyle.danger)
    async def refuse(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.poster.id:
            await interaction.response.send_message("❌ You are not allowed to make this decision.", ephemeral=True)
            return

        await interaction.response.edit_message(
            content="❌ You refused the DM request.",
            embed=None,
            view=None
        )
        await self.replier.send("❌ Your DM request was refused by the user.")

# ==============================
# ROLE SELECT
# ==============================
class RoleSelectView(View):
    def __init__(self):
        super().__init__(timeout=60)
        self.select = Select(
            placeholder="Looking for...",
            options=[discord.SelectOption(label=l) for l in config.ROLE_SELECT_OPTIONS]
        )
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction):
        await interaction.response.send_modal(
            PostMessageModal(self.select.values[0])
        )

# ==============================
# MESSAGE BUTTONS
# ==============================
class MessageButtons(View):
    def __init__(self, mid):
        super().__init__(timeout=None)
        self.mid = mid

    @discord.ui.button(label="Post", style=discord.ButtonStyle.success)
    async def post(self, interaction, _):
        await interaction.response.send_message(
            "📝 Select who you're looking for:",
            view=RoleSelectView(),
            ephemeral=True
        )

    @discord.ui.button(label="Reply", style=discord.ButtonStyle.primary)
    async def reply(self, interaction, _):
        await interaction.response.send_modal(ReplyModal(self.mid))

    @discord.ui.button(label="DM", style=discord.ButtonStyle.secondary)
    async def dm(self, interaction, _):
        uid = message_authors.get(self.mid)
        if not uid:
            await interaction.response.send_message("❌ User not found.", ephemeral=True)
            return

        poster = await bot.fetch_user(uid)
        await interaction.response.send_modal(DMMessageModal(poster))

    @discord.ui.button(label="Report", style=discord.ButtonStyle.danger)
    async def report(self, interaction, _):
        log = interaction.guild.get_channel(config.MOD_LOG_CHANNEL_ID)
        message_link = f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{self.mid}"

        embed = discord.Embed(
            title="⚠️ Reported Message",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="🔗 Message Link", value=message_link, inline=False)
        embed.add_field(name="👤 Reporter", value=interaction.user.mention, inline=False)

        await log.send(embed=embed)
        await interaction.response.send_message("✅ Report sent.", ephemeral=True)

# ==============================
# COMMAND
# ==============================
@bot.command()
async def post(ctx):
    await ctx.send(
        "📝 Start an anonymous message:",
        view=MessageButtons(None)
    )
    if config.CONFESSION_RULES.get("delete_command", True):
        await ctx.message.delete()

# ==============================
# READY
# ==============================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ==============================
# RUN
# ==============================
bot.run(TOKEN)
