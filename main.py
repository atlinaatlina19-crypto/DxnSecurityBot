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

# إعدادات البوت بدون تفعيل حالة الصوت لتجنب مشاكل بايثون 3.14
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)
user_messages = {}

@bot.event
async def on_ready():
    print(f'✅ Security Bot Logged in as: {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands(s)")
    except Exception as e:
        print(e)
    
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="🛡️ Protecting Server & Anti-Nuke"
    ))

# 🗑️ أمر سلاش لحذف جميع رومات السيرفر: /deletechannels
@bot.tree.command(name="deletechannels", description="حذف جميع رومات السيرفر (تحذير: خطير!)")
@commands.has_permissions(administrator=True)
async def slash_delete_channels(interaction: discord.Interaction):
    await interaction.response.send_message("⚠️ جاري حذف جميع رومات السيرفر...", ephemeral=True)
    for channel in interaction.guild.channels:
        try:
            await channel.delete()
        except Exception as e:
            print(f"Failed to delete channel {channel.name}: {e}")

# 🗑️ أمر سلاش لحذف جميع رتب السيرفر: /deleteroles
@bot.tree.command(name="deleteroles", description="حذف جميع رتب السيرفر (تحذير: خطير!)")
@commands.has_permissions(administrator=True)
async def slash_delete_roles(interaction: discord.Interaction):
    await interaction.response.send_message("⚠️ جاري حذف جميع رتب السيرفر...", ephemeral=True)
    for role in interaction.guild.roles:
        if role.is_default() or role == interaction.guild.me.top_role or role >= interaction.guild.me.top_role:
            continue
        try:
            await role.delete()
        except Exception as e:
            print(f"Failed to delete role {role.name}: {e}")

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

bot.run(os.environ.get('DISCORD_TOKEN'))
