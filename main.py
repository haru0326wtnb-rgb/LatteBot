import discord
from discord.ext import commands

# 1. 自分の新しいトークンをここに貼り付けてください
TOKEN = "MTUxMDk5MTIwMDc5NzIwMDM4NA.GlvJN1.NAV3KSlDezLyMuw8OPLXueqRFTo_CVHSGVG7Jk"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

custom_roles = ["論争厨", "平和民", "イラストかける", "荒らし民", "bot作れる", "編集できる", "雑談する！"]

# --- 1. 認証システム ---
class VerifyModal(discord.ui.Modal, title="王国への入国申請"):
    source = discord.ui.TextInput(label="どこのアプリから来ましたか？", placeholder="SNS, 知人の紹介など")
    read_rules = discord.ui.TextInput(label="ルールを読みましたか？", placeholder="はい")

    async def on_submit(self, interaction: discord.Interaction):
        if self.read_rules.value.lower() != "はい":
            await interaction.response.send_message("ルール未読のため拒否されました。", ephemeral=True)
            return
        role = discord.utils.get(interaction.guild.roles, name="Member")
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("認証完了！王国へようこそ。", ephemeral=True)
            log = discord.utils.get(interaction.guild.text_channels, name="管理ログ")
            if log:
                await log.send(f"【入国】{interaction.user.mention} (経緯: {self.source.value})")

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="入国申請する", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())

# --- 2. ロール選択システム ---
class DynamicRoleSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=r, value=r) for r in custom_roles]
        super().__init__(placeholder="興味のある役職を選んでね", options=options, custom_id="role_select_menu")
    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"{role.name} を付与しました！", ephemeral=True)

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DynamicRoleSelect())

# --- 3. 起動とイベント ---
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    bot.add_view(RoleView())
    print(f"{bot.user} で起動しました！")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if len(message.mentions) >= 5:
        await message.delete()
        await message.channel.send("スパム検知：削除しました。")
    if "http" in message.content and message.channel.name != "宣伝":
        await message.delete()
        await message.channel.send("URLは「宣伝」チャンネルに投稿してください。")
    await bot.process_commands(message)

# --- 4. コマンド ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    await ctx.send("【入国認証】ボタンを押して申請:", view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_roles(ctx):
    await ctx.send("【役職選択】自分に付与したい役職を選んでください:", view=RoleView())

bot.run("MTUxMDk5MTIwMDc5NzIwMDM4NA.GlvJN1.NAV3KSlDezLyMuw8OPLXueqRFTo_CVHSGVG7Jk")