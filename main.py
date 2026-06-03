import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# --- (中略：以前のコードはそのまま) ---

# --- Webサーバーのフリをするためのコード ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

# スレッドを起動
t = Thread(target=run)
t.start()

# --- 起動 ---
bot.run(os.environ['TOKEN'])
