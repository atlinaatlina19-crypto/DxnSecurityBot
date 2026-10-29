import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread

# إعداد سيرفر Flask لعمل الـ Ping وإبقاء البوت مستيقظاً 24/7
app = Flask('')

@app.route('/')
def home():
    return "==> Your service is live 🚀"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# إعداد بوت ديسكورد مع الصلاحيات (Intents)
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    try:
        # مزامنة أوامر الـ Slash Commands تلقائياً مع ديسكورد
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# أمر الـ Slash Command للانضمام إلى الروم الصوتي
@bot.tree.command(name="join", description="يجعل البوت ينضم إلى الروم الصوتي الخاص بك")
async def join(interaction: discord.Interaction):
    if interaction.user.voice and interaction.user.voice.channel:
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        await interaction.response.send_message(f"تم الانضمام بنجاح إلى الروم: **{channel.name}** ✅", ephemeral=True)
    else:
        await interaction.response.send_message("يجب أن تكون متصلاً بروم صوتي أولاً لكي أتمكن من الدخول!", ephemeral=True)

# تشغيل خادم الويب أولاً ثم تشغيل البوت باستخدام التوكن من المتغيرات البيئية
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN environment variable not found!")
    else:
        bot.run(TOKEN)
