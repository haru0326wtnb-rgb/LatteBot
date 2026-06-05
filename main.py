import discord
from discord.ext import commands
import os
import datetime
from collections import defaultdict
from flask import Flask
from threading import Thread

# --- 1. Webサーバー ---
app = Flask(__name__)
@app.route('/')
def home(): return "Kingdom Bot is online."
Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()

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

user_actions = defaultdict(list)
lockdown_mode = False

# --- 3. 国王コマンド（整理済み） ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_reaction(ctx):
    """住民ロール選択メッセージを設置"""
    embed = discord.Embed(title="🔱 住民の役割を選択しよう", description="\n".join([f"{k} : {v}" for k, v in ROLE_MAP.items()]), color=discord.Color.gold())
    msg = await ctx.send(embed=embed)
    for emoji in ROLE_MAP.keys(): 
        await msg.add_reaction(emoji)
    await ctx.send(f"✅ 設定完了！このメッセージのID: **{msg.id}** を環境変数の ROLE_MSG_ID に設定してください。")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_entry(ctx):
    """入国審査ボタンを設置"""
    await ctx.send("【入国申請所】", view=EntryView())

@bot.command()
@commands.has_role("国王")
async def lockdown(ctx, mode: str):
    global lockdown_mode
    lockdown_mode = (mode == "on")
    await ctx.send(f"🚨 【防衛】ロックダウン: {'発動中' if lockdown_mode else '解除済み'}")

# --- 4. ロジック ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    # 国王免除
    if any(r.name == "国王" for r in message.author.roles) or message.author.guild_permissions.administrator:
        await bot.process_commands(message)
        return
    # 防衛ロジック
    if lockdown_mode: await message.delete()
    elif any(p in message.content.lower() for p in ["@everyone", "@here", "discord.gg/", "http"]) or len(message.mentions) >= 5:
        await message.delete()
    else:
        now = datetime.datetime.now()
        user_actions[message.author.id].append(now)
        if len([t for t in user_actions[message.author.id] if (now - t).seconds < 5]) > 5:
            await message.author.kick(reason="AI検知：スパム")
            return
        await bot.process_commands(message)

class EntryView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="らて王国に入国する", style=discord.ButtonStyle.primary, custom_id="entry_button")
    async def entry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if (datetime.datetime.now(datetime.timezone.utc) - interaction.user.created_at).days < 7:
            await interaction.followup.send("入国拒否：アカウントが新しすぎます。", ephemeral=True)
            return
        role = discord.utils.get(interaction.guild.roles, name="Member")
        if role:
            await interaction.user.add_roles(role)
            await interaction.followup.send("入国しました！", ephemeral=True)
            try: await interaction.user.send("入国ありがとう！次は「国民申請届」チャンネルへどうぞ。")
            except: pass

@bot.event
async def on_raw_reaction_add(payload):
    msg_id = os.environ.get('ROLE_MSG_ID')
    if payload.member.bot or not msg_id or payload.message_id != int(msg_id): return
    role = discord.utils.get(payload.member.guild.roles, name=ROLE_MAP.get(str(payload.emoji)))
    if role: await payload.member.add_roles(role)

@bot.event
async def on_ready():
    bot.add_view(EntryView())
    print("【防衛要塞：起動完了】")

bot.run(os.environ.get('TOKEN'))
