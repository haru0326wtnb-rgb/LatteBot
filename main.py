import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# --- 1. Webサーバー ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# --- 2. 設定 ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

ROLE_MAP = {
    "🗣️": "論争厨", "🕊️": "平和民", "🎨": "イラストかける",
    "💥": "荒らし民", "🤖": "bot作れる", "✍️": "編集できる", "💬": "雑談する！"
}

# --- 3. 入国ボタンロジック ---
class EntryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="らて王国に入国する", style=discord.ButtonStyle.primary, custom_id="entry_button")
    async def entry_button(self, interaction: discord.Interaction, button: discord.ui.button):
        # 処理を開始したことを通知（エラーを回避するため）
        await interaction.response.defer(ephemeral=True)
        
        role = discord.utils.get(interaction.guild.roles, name="Member")
        if not role:
            await interaction.followup.send("エラー: 'Member' という名前のロールが見つかりません。サーバー設定を確認してください。", ephemeral=True)
            return
            
        try:
            await interaction.user.add_roles(role)
            await interaction.followup.send("入国しました！ようこそらて王国へ！", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("エラー: ボットに権限がありません（ロールの順序を確認してください）。", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: {e}", ephemeral=True)

# --- 4. イベント ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    # ボタンの同期
    bot.add_view(EntryView())
    print("ボタンの同期完了！")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.bot or payload.message_id != int(os.environ.get('ROLE_MSG_ID', 0)): return
    try:
        role = discord.utils.get(payload.member.guild.roles, name=ROLE_MAP.get(str(payload.emoji)))
        if role: await payload.member.add_roles(role)
    except: pass

@bot.event
async def on_message(message):
    if message.author.bot: return
    # 荒らし対策
    content = message.content.lower()
    if any(word in content for word in ["@everyone", "@here", "discord.gg/"]) or len(message.mentions) >= 5:
        try: await message.delete()
        except: pass
    await bot.process_commands(message)

# --- 5. コマンド ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_entry(ctx):
    embed = discord.Embed(title="入国申請所", description="下のボタンを押して入国！", color=discord.Color.green())
    await ctx.send(embed=embed, view=EntryView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_reaction(ctx):
    embed = discord.Embed(title="🔱 住民の役割を選択しよう", description="\n".join([f"{k} : {v}" for k, v in ROLE_MAP.items()]), color=discord.Color.gold())
    msg = await ctx.send(embed=embed)
    for emoji in ROLE_MAP.keys(): await msg.add_reaction(emoji)
    await ctx.send(f"ID: **{msg.id}** を環境変数へ")

bot.run(os.environ['TOKEN'])
