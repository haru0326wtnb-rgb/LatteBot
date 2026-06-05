import discord
from discord.ext import commands
import os
import datetime
from collections import defaultdict
from flask import Flask
from threading import Thread

# --- 1. Webサーバー (Render監視用) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Kingdom Bot is online."
Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()

# --- 2. 設定・初期化 ---
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

# --- 3. 防衛・免除ロジック ---
@bot.event
async def on_message(message):
    if message.author.bot: return

    # 国王免除（国王ロールまたは管理者権限）
    if any(r.name == "国王" for r in message.author.roles) or message.author.guild_permissions.administrator:
        await bot.process_commands(message)
        return

    # 緊急ロックダウン
    if lockdown_mode:
        await message.delete()
        return

    # スパム・URL・メンション対策
    content = message.content.lower()
    if any(p in content for p in ["@everyone", "@here", "discord.gg/", "http"]) or len(message.mentions) >= 5:
        await message.delete()
        return

    # AI挙動分析（スパム連投検知）
    now = datetime.datetime.now()
    user_actions[message.author.id].append(now)
    if len([t for t in user_actions[message.author.id] if (now - t).seconds < 5]) > 5:
        await message.author.kick(reason="AI検知：スパム行動")
        return

    await bot.process_commands(message)

# --- 4. 入国システム (DM誘導付き) ---
class EntryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="らて王国に入国する", style=discord.ButtonStyle.primary, custom_id="entry_button")
    async def entry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        # 捨て垢対策（7日未満拒否）
        if (datetime.datetime.now(datetime.timezone.utc) - interaction.user.created_at).days < 7:
            await interaction.followup.send("入国拒否：アカウントが新しすぎます。", ephemeral=True)
            return
        
        role = discord.utils.get(interaction.guild.roles, name="Member")
        if role:
            await interaction.user.add_roles(role)
            await interaction.followup.send("入国しました！", ephemeral=True)
            try:
                await interaction.user.send("入国ありがとう！次は「国民申請届」というチャンネルで「国民になりたいです」と発言してね！")
            except discord.Forbidden:
                await interaction.followup.send("入国完了！DMが送れないため、チャンネルで申請してください。", ephemeral=True)

# --- 5. 国王専用コマンド ---
@bot.command()
@commands.has_role("国王")
async def lockdown(ctx, mode: str):
    global lockdown_mode
    lockdown_mode = (mode == "on")
    await ctx.send(f"🚨 【防衛】ロックダウン: {'発動中' if lockdown_mode else '解除済み'}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_entry(ctx):
    await ctx.send("【入国申請所】", view=EntryView())

@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.bot or payload.message_id != int(os.environ.get('ROLE_MSG_ID', 0)): return
    role = discord.utils.get(payload.member.guild.roles, name=ROLE_MAP.get(str(payload.emoji)))
    if role: await payload.member.add_roles(role)

@bot.event
async def on_ready():
    bot.add_view(EntryView())
    print("【防衛要塞：起動完了】")

bot.run(os.environ.get('TOKEN'))
