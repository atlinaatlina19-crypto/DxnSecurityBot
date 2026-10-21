import os
import time
import asyncio
from threading import Thread
import discord
from discord.ext import commands
from flask import Flask

# خادم الويب للحفاظ على نشاط البوت 24/7
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

# إعدادات البوت
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
user_messages = {}

@bot.event
async def on_ready():
    print(f'✅ Security Bot Logged in as: {bot.user}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="🛡️ Protecting Server & Anti-Nuke"
    ))

# 🎙️ أمر يدوي لدخول البوت إلى الروم الصوتي فوراً
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.guild.voice_client is not None:
            await ctx.guild.voice_client.move_to(channel)
        else:
            await channel.connect(reconnect=True, self_deaf=True)
        await ctx.send(f"🎙️ دخلت معك للروم الصوتي: **{channel.name}**!", delete_after=5)
    else:
        await ctx.send("⚠️ يجب أن تكون داخل روم صوتي أولاً لكي أتمكن من الدخول معك!", delete_after=5)

# أمر إخراج البوت من الروم (إذا احتجت له)
@bot.command()
async def leave(ctx):
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("👋 طلعت من الروم الصوتي.", delete_after=5)

# -------------------- حماية الرومات (إنشاء / حذف) --------------------
async def ban_attacker(guild, entry, reason):
    try:
        async for log in guild.audit_logs(limit=1, action=entry):
            user = log.user
            if user.id != bot.user.id and user.id != guild.owner_id:
                await guild.ban(user, reason=f"🚨 نظام الحماية: {reason}")
                print(f"🔨 BANNED: {user.name} | Reason: {reason}")
                return
    except Exception as e:
        print(f"Error fetching audit logs: {e}")

@bot.event
async def on_guild_channel_create(channel):
    await ban_attacker(channel.guild, discord.AuditLogAction.channel_create, f"إنشاء روم جديد ({channel.name})")

@bot.event
async def on_guild_channel_delete(channel):
    await ban_attacker(channel.guild, discord.AuditLogAction.channel_delete, f"حذف روم ({channel.name})")

# -------------------- حماية الرتب (إنشاء / تعديل / حذف) --------------------
@bot.event
async def on_guild_role_create(role):
    await ban_attacker(role.guild, discord.AuditLogAction.role_create, f"إنشاء رتبة جديدة ({role.name})")

@bot.event
async def on_guild_role_delete(role):
    await ban_attacker(role.guild, discord.AuditLogAction.role_delete, f"حذف رتبة ({role.name})")

@bot.event
async def on_guild_role_update(before, after):
    if before.name != after.name or before.permissions != after.permissions:
        await ban_attacker(after.guild, discord.AuditLogAction.role_update, f"تعديل على رتبة ({before.name})")

# -------------------- حماية الدردشة من السبام والروابط --------------------
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    if ('http://' in message.content or 'https://' in message.content) and not message.author.guild_permissions.administrator:
        await message.delete()
        await message.channel.send(f"⚠️ {message.author.mention}، يمنع نشر الروابط!", delete_after=4)
        return

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

# أوامر الإدارة العامة
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 تم مسح {amount} رسالة!", delete_after=3)

bot.run(os.environ.get('DISCORD_TOKEN'))
