import os
import time
from threading import Thread
import discord
from discord.ext import commands
from flask import Flask

# -------------------- خادم الويب (Keep Alive) --------------------
app = Flask('')


@app.route('/')
def home():
  return "Security Bot is Active!"


def run():
  app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))


def keep_alive():
  t = Thread(target=run)
  t.daemon = True
  t.start()


keep_alive()

# -------------------- إعدادات البوت --------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ذاكرة مؤقتة لمنع السبام
user_messages = {}


@bot.event
async def on_ready():
  print(f'✅ Security Bot Logged in as: {bot.user}')
  # تغيير حالة البوت إلى "يحمي السيرفر"
  await bot.change_presence(
      activity=discord.Activity(
          type=discord.ActivityType.watching, name="🛡️ Protecting the server"
      )
  )


# -------------------- 1. حماية ضد الروابط والسبام --------------------
@bot.event
async def on_message(message):
  if message.author.bot:
    return

  # أ) منع الروابط الخارجية (باستثناء المشرفين)
  if (
      'http://' in message.content or 'https://' in message.content
  ) and not message.author.guild_permissions.administrator:
    await message.delete()
    await message.channel.send(
        f'⚠️ {message.author.mention}، يمنع نشر الروابط في هذا السيرفر!',
        delete_after=5,
    )
    return

  # ب) منع التكرار والسبام (Anti-Spam)
  user_id = message.author.id
  current_time = time.time()

  if user_id not in user_messages:
    user_messages[user_id] = []

  # احتفاظ بتوقيت آخر الرسائل
  user_messages[user_id].append(current_time)
  user_messages[user_id] = [
      t for t in user_messages[user_id] if current_time - t < 3
  ]

  # إذا أرسل أكثر من 5 رسائل في أقل من 3 ثوانٍ
  if (
      len(user_messages[user_id]) > 5
      and not message.author.guild_permissions.administrator
  ):
    await message.channel.purge(limit=5, check=lambda m: m.author == message.author)
    await message.channel.send(
        f'🚨 {message.author.mention} تم رصد سبام! تم مسح رسائلك.', delete_after=5
    )
    return

  await bot.process_commands(message)


# -------------------- 2. أوامر الإدارة والحماية --------------------
# أمر مسح الشات (Clear)
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
  await ctx.channel.purge(limit=amount + 1)
  await ctx.send(f'🧹 تم مسح {amount} رسالة بنجاح!', delete_after=3)


# أمر الحظر (Ban)
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason='لا يوجد سبب'):
  await member.ban(reason=reason)
  await ctx.send(f'🔨 تم حظر {member.mention} | السبب: {reason}')


# أمر الطرد (Kick)
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason='لا يوجد سبب'):
  await member.kick(reason=reason)
  await ctx.send(f'👢 تم طرد {member.mention} | السبب: {reason}')


# -------------------- تشغيل البوت --------------------
bot.run(os.environ.get('DISCORD_TOKEN'))
