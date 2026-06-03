import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# Webサーバー用
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# 設定
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 認証・役職用クラス
class VerifyModal(discord.ui.Modal, title="入国申請"):
    source = discord.ui.TextInput(label="どこから来ましたか？")
    async def on_submit(self, interaction):
        await interaction.response.send_message("申請完了！管理者が確認します。", ephemeral=True)

class VerifyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="入国申請", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify(self, interaction, button): await interaction.response.send_modal(VerifyModal())

class RoleView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="住民になる", style=discord.ButtonStyle.primary, custom_id="role_member")
    async def add_member(self, interaction, button):
        role = discord.utils.get(interaction.guild.roles, name="Member")
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("身分証を付与しました！", ephemeral=True)

# スパム対策
@bot.event
async def on_message(message):
    if message.author.bot: return
    content = message.content.lower()
    if "@everyone" in content or "@here" in content or "discord.gg/" in content or len(message.mentions) >= 5:
        try:
            await message.delete()
            await message.channel.send(f"{message.author.mention} スパム行為を検知したため削除しました。", delete_after=5)
        except: pass
        return
    await bot.process_commands(message)

@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    bot.add_view(RoleView())
    print(f"らて王国ボット {bot.user} 稼働中")

# 管理用コマンド
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx): await ctx.send("🏰 **入国ゲート**", view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_roles(ctx): await ctx.send("📜 **身分証の発行**", view=RoleView())

@bot.command()
@commands.has_permissions(administrator=True)
async def backup_link(ctx):
    template = await ctx.guild.create_template(name="らて王国バックアップ")
    await ctx.send(f"バックアップ（テンプレート）を作成しました。このURLから復元可能です:\n{template.url}")

bot.run(os.environ['TOKEN'])
