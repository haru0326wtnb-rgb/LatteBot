import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# Webサーバー用（Render対策）
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running!"
def run_web():
    app.run(host='0.0.0.0', port=8080)
t = Thread(target=run_web)
t.start()

# Discordボット設定
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 入国申請用モーダル
class VerifyModal(discord.ui.Modal, title="王国への入国申請"):
    source = discord.ui.TextInput(label="どこのアプリから来ましたか？")
    read_rules = discord.ui.TextInput(label="ルールを読みましたか？", placeholder="はい")
    async def on_submit(self, interaction: discord.Interaction):
        if self.read_rules.value.lower() != "はい":
            await interaction.response.send_message("ルール未読のため拒否されました。", ephemeral=True)
            return
        role = discord.utils.get(interaction.guild.roles, name="Member")
        if role: await interaction.user.add_roles(role)
        await interaction.response.send_message("認証完了！らて王国へようこそ。", ephemeral=True)
        log = discord.utils.get(interaction.guild.text_channels, name="管理ログ")
        if log: await log.send(f"【入国】{interaction.user.mention} が新たに入国しました！")

class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="入国申請する", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify(self, interaction, button): await interaction.response.send_modal(VerifyModal())

# イベント処理
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    print(f"{bot.user} で起動しました！")

@bot.event
async def on_member_join(member):
    log = discord.utils.get(member.guild.text_channels, name="管理ログ")
    if log: await log.send(f"【入国】{member.mention} がやってきました！")

@bot.event
async def on_message(message):
    if message.author.bot: return
    # スパム対策
    if len(message.mentions) >= 5:
        await message.delete()
        await message.channel.send("スパム検知：削除しました。")
    # コマンドを有効にするために必須！
    await bot.parse_commands(message) # 旧 process_commands 相当
    await bot.process_commands(message)

# コマンド
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(title="🏰 王国の正門", description="入国を希望する者はボタンを押して申請しなさい。", color=discord.Color.gold())
    await ctx.send(embed=embed, view=VerifyView())

# 起動
bot.run(os.environ['TOKEN'])
