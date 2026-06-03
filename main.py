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
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ロール設定
ROLE_MAP = {
    "🗣️": "論争厨", "🕊️": "平和民", "🎨": "イラストかける",
    "💥": "荒らし民", "🤖": "bot作れる", "✍️": "編集できる", "💬": "雑談する！"
}

# --- 機能ロジック ---
@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.bot or payload.message_id != int(os.environ.get('ROLE_MSG_ID', 0)): return
    role = discord.utils.get(payload.member.guild.roles, name=ROLE_MAP.get(str(payload.emoji)))
    if role: await payload.member.add_roles(role)

@bot.event
async def on_message(message):
    if message.author.bot: return
    # スパム対策
    content = message.content.lower()
    if "@everyone" in content or "@here" in content or "discord.gg/" in content or len(message.mentions) >= 5:
        await message.delete()
        return
    await bot.process_commands(message)

# --- コマンド ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_reaction(ctx):
    embed = discord.Embed(title="🔱 住民の役割を選択しよう", description="\n".join([f"{k} : {v}" for k, v in ROLE_MAP.items()]), color=discord.Color.gold())
    msg = await ctx.send(embed=embed)
    for emoji in ROLE_MAP.keys(): await msg.add_reaction(emoji)
    await ctx.send(f"このメッセージIDをコピーしてRenderの環境変数 'ROLE_MSG_ID' に設定してください: **{msg.id}**")

@bot.command()
@commands.has_permissions(administrator=True)
async def backup_link(ctx):
    template = await ctx.guild.create_template(name="らて王国バックアップ")
    await ctx.send(f"バックアップ用テンプレート: {template.url}")

bot.run(os.environ['TOKEN'])
