import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# 1. Webサーバー機能（Render対策）
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running!"
def run_web():
    app.run(host='0.0.0.0', port=8080)
t = Thread(target=run_web)
t.start()

# 2. ボットの定義
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 3. 各種システム
class VerifyModal(discord.ui.Modal, title="王国への入国申請"):
    source = discord.ui.TextInput(label="どこのアプリから来ましたか？")
    read_rules = discord.ui.TextInput(label="ルールを読みましたか？", placeholder="はい")
    async def on_submit(self, interaction: discord.Interaction):
        if self.read_rules.value.lower() != "はい": return
        role = discord.utils.get(interaction.guild.roles, name="Member")
        if role: await interaction.user.add_roles(role)
        await interaction.response.send_message("認証完了！", ephemeral=True)

class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="入国申請する", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify(self, interaction, button): await interaction.response.send_modal(VerifyModal())

# 4. 新規入会通知
@bot.event
async def on_member_join(member):
    log = discord.utils.get(member.guild.text_channels, name="管理ログ")
    if log: await log.send(f"【入国】{member.mention} が王国にやってきました！")

# 5. その他
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    print(f"{bot.user} で起動しました！")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if len(message.mentions) >= 5:
        await message.delete()
        await message.channel.send("スパム検知：削除しました。")
    await bot.process_commands(message)

# 6. 実行
bot.run(os.environ['TOKEN'])
