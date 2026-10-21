import os
import time
import asyncio
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
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ⚙️ إعدادات الحماية والتواجد الصوتي (قم بتعديل الآيدي)
VOICE_CHANNEL_ID = 1560311266147442708  # 👈 ضع آيدي الروم الصوتي هنا للبقاء فيه 24/7
user_messages = {}

# -------------------- دالة الأونلاين والتواجد الصوتي --------------------
@bot.event
async def on_ready():
    print(f'✅ Security Bot Logged in as: {bot.user}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="🛡️ Protecting Server & Anti-Nuke"
    ))
    
    # الانضمام التلقائي للروم الصوتي
    await join_voice_channel()

async def join_voice_channel():
    await bot.wait_until_ready()
    try:
        channel = bot.get_channel(VOICE_CHANNEL_ID)
        if channel and isinstance(channel, discord.VoiceChannel):
            if not channel.guild.voice_client:
                await channel.connect(reconnect=True, self_deaf=True)
                print(f"🎙️ Connected to voice channel: {channel.name}")
    except Exception as e:
        print(f"❌ Voice connection error: {e}")

# إعادة الاتصال بالروم الصوتي إذا فصل البوت
@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user and after.channel is None:
        await asyncio.sleep(5)
        await join_voice_channel()

# -------------------- دالة المعاقبة الحسابية (Ban Attacker) --------------------
async def ban_attacker(guild, entry, reason):
    """البحث عن الشخص المسؤول في سجل النشاطات (Audit Logs) وحظره فوراً"""
    try:
        async for log in guild.audit_logs(limit=1, action=entry):
            user = log.user
            # يتجاهل البوت نفسه ومالك السيرفر
            if user.id != bot.user.id and user.id != guild.owner_id:
                await guild.ban(user, reason=f"🚨 نظام الحماية: {reason}")
                print(f"🔨 BANNED: {user.name} | Reason: {reason}")
                return
    except Exception as e:
        print(f"Error fetching audit logs: {e}")

# -------------------- 1. حماية الرومات (إنشاء / حذف) --------------------
@bot.event
async def on_guild_channel_create(channel):
    """حظر الشخص الذي أنشأ روم بدون إذن"""
    await ban_attacker(channel.guild, discord.AuditLogAction.channel_create, f"إنشاء روم جديد ({channel.name})")

@bot.event
async def on_guild_channel_delete(channel):
    """حظر الشخص الذي حذف روم"""
    await ban_attacker(channel.guild, discord.AuditLogAction.channel_delete, f"حذف روم ({channel.name})")

# -------------------- 2. حماية الرتب (إنشاء / تعديل / حذف) --------------------
@bot.event
async def on_guild_role_create(role):
    """حظر الشخص الذي أنشأ رتبة جديدة"""
    await ban_attacker(role.guild, discord.AuditLogAction.role_create, f"إنشاء رتبة جديدة ({role.name})")

@bot.event
async def on_guild_role_delete(role):
    """حظر الشخص الذي حذف رتبة"""
    await ban_attacker(role.guild, discord.AuditLogAction.role_delete, f"حذف رتبة ({role.name})")

@bot.event
async def on_guild_role_update(before, after):
    """حظر الشخص الذي غير اسم أو صلاحيات رتبة"""
    if before.name != after.name or before.permissions != after.permissions:
        await ban_attacker(after.guild, discord.AuditLogAction.role_update, f"تعديل على رتبة ({before.name})")

# -------------------- 3. حماية الدردشة من السبام والروابط --------------------
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # أ) منع الروابط الخارجية (لغير المشرفين)
    if ('http://' in message.content or 'https://' in message.content) and not message.author.guild_permissions.administrator:
        await message.delete()
        await message.channel.send(f"⚠️ {message.author.mention}، يمنع نشر الروابط!", delete_after=4)
        return

    # ب) منع التكرار والسبام (Anti-Spam)
    user_id = message.author.id
    current_time = time.time()
    
    if user_id not in user_messages:
        user_messages[user_id] = []
        
    user_messages[user_id].append(current_time)
    user_messages[user_id] = [t for t in user_messages[user_id] if current_time - t < 3]

    if len(user_messages[user_id]) > 5 and not message.author.guild_permissions.administrator:
        await message.channel.purge(limit=5, check=lambda m: m.author == message.author)
        await message.channel.send(f"🚨 {message.author.mention} تم رصد سبام! تم مسح رسائلك.", delete_after=5)
        return

    await bot.process_commands(message)

# -------------------- 4. أوامر الإدارة العامة --------------------
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 تم مسح {amount} رسالة!", delete_after=3)

# -------------------- تشغيل البوت --------------------
bot.run(os.environ.get('DISCORD_TOKEN'))
