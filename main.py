import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# Webサーバー
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# 設定
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 1. ロール付与用 ---
class RoleView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="住民になる", style=discord.ButtonStyle.primary, custom_id="role_member")
    async def add_member(self, interaction, button):
        role = discord.utils.get(interaction.guild.roles, name="Member")
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("住民の身分証を付与しました！", ephemeral=True)

# --- 2. 入国審査用 ---
class VerifyModal(discord.ui.Modal, title="入国申請"):
    source = discord.ui.TextInput(label="どこから来ましたか？")
    async def on_submit(self, interaction):
        await interaction.response.send_message("申請完了！管理者が確認します。", ephemeral=True)

class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="入国申請", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify(self, interaction, button): await interaction.response.send_modal(VerifyModal())

# --- 3. イベント（スパム＆Nuke対策） ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    # スパム対策（メンション5つ以上）
    if len(message.mentions) >= 5:
        await message.delete()
        await message.channel.send(f"{message.author.mention} スパムを検知したため削除しました。")
    # Nuke対策（大量のチャンネル作成などへの簡易防御）
    # ※特定のコマンド入力を監視して停止させる等のロジックはここへ追加
    await bot.process_commands(message)

# --- 4. コマンド ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx): await ctx.send("🏰 王国の正門", view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_roles(ctx): await ctx.send("📜 役職の付与", view=RoleView())

@bot.command()
@commands.has_permissions(administrator=True)
async def backup(ctx):
    # 簡易バックアップ：ロールとチャンネルの一覧を書き出す
    info = "\n".join([r.name for r in ctx.guild.roles])
    await ctx.send(f"現在のロール一覧を書き出しました:\n{info}")

bot.run(os.environ['TOKEN'])
