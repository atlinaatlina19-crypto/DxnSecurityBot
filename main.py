import os
from threading import Thread
import discord
from flask import Flask

app = Flask('')


@app.route('/')
def home():
  return "Bot is alive!"


def run():
  app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))


def keep_alive():
  t = Thread(target=run)
  t.daemon = True
  t.start()


# تشغيل خادم الويب للحفاظ على نشاط البوت
keep_alive()

# إعدادات بوت الديسكورد الأساسية
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)


@bot.event
async def on_ready():
  print(f'Logged in as {bot.user}')


# تشغيل البوت مع وضع التوكن الخاص بك هنا بين علامتي التنصيص
bot.run('MTU2MjExMjMzMjI3OTA1X0Fqhn3T.VkoKW_msRjLgCWeq9JVqFQe6huC1Nku0gAmSWa')
