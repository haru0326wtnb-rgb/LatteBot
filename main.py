import discord
from discord.ext import commands
import os
import datetime
from collections import defaultdict

# --- 設定 ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 状態管理用
user_actions = defaultdict(list)
lockdown_mode = False

# --- 国王専用コマンド ---
@bot.command()
@commands.has_role("国王")
async def security(ctx, action: str):
    """
    !security lock : ロックダウン発動（全発言制限）
    !security unlock : ロックダウン解除
    !security clear : 直近の荒らしログをクリア
    """
    global lockdown_mode
    if action == "lock":
        lockdown_mode = True
        await ctx.send("🚨 【緊急防衛】ロックダウンを発動しました。すべての発言を制限します。")
    elif action == "unlock":
        lockdown_mode = False
        await ctx.send("✅ 【防衛解除】通常モードへ戻りました。")

@bot.command()
@commands.has_role("国王")
async def ban_user(ctx, user_id: int):
    """ 指定IDを強制BANし、データベースへ追加 """
    # ここにDB登録処理を記述
    await ctx.send(f"🛡️ ユーザー {user_id} を永久追放リストに追加しました。")

# --- 防衛ロジック（自動化完結型） ---
@bot.event
async def on_message(message):
    if message.author.bot: return

    # 国王免除
    if "国王" in [r.name for r in message.author.roles] or message.author.guild_permissions.administrator:
        await bot.process_commands(message)
        return

    # 【1】ロックダウン中の全削除
    if lockdown_mode:
        await message.delete()
        return

    # 【2】自動フィルタ（メンション・URL）
    if any(p in message.content.lower() for p in ["@everyone", "@here", "http"]) or len(message.mentions) >= 5:
        await message.delete()
        return

    # 【3】自動スパム検知
    now = datetime.datetime.now()
    user_actions[message.author.id].append(now)
    if len([t for t in user_actions[message.author.id] if (now - t).seconds < 5]) > 5:
        await message.author.kick(reason="自動防衛：スパム検知")
        return

    await bot.process_commands(message)

# --- 入国システム ---
class EntryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="入国審査", style=discord.ButtonStyle.green, custom_id="entry_v2")
    async def entry(self, interaction: discord.Interaction, button: discord.ui.Button):
        # アカウント年齢判定（7日未満拒否）
        if (datetime.datetime.now(datetime.timezone.utc) - interaction.user.created_at).days < 7:
            await interaction.response.send_message("入国拒否。", ephemeral=True)
            return
        
        role = discord.utils.get(interaction.guild.roles, name="Member")
        await interaction.user.add_roles(role)
        await interaction.response.send_message("入国完了。", ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(EntryView())
    print("【防衛システム：待機中】")

bot.run(os.environ.get('TOKEN'))
