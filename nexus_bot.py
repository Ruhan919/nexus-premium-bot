"""
╔══════════════════════════════════════════════════════════════╗
║     🤖 NEXUS PREMIUM BOT — ULTIMATE EDITION v5.0           ║
╠══════════════════════════════════════════════════════════════╣
║  👑 Engine: NEXUS MULTI-API ENGINE                         ║
║  ⚡ Features: Multi-API | Group Mgmt | Auto-Like | VIP     ║
║  🔐 Security: Rate Limited | Verified | Logged | Admin     ║
║  💎 Credits: VIP DARK GOD                                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import telegram
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import requests
import json
import os
import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz
    from datetime import timezone
    class ZoneInfo:
        def __init__(self, key):
            self._tz = pytz.timezone(key)
        def utcoffset(self, dt):
            return self._tz.utcoffset(dt)
        def fromutc(self, dt):
            return self._tz.fromutc(dt)
        def tzname(self, dt):
            return self._tz.tzname(dt)
        def localize(self, dt, is_dst=False):
            return self._tz.localize(dt, is_dst=is_dst)
        def __str__(self):
            return str(self._tz)
import tempfile
import shutil
import re
import time
import sys
import traceback
import random
import string
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any, Union, Callable

# ====================================================================================================
#                                               VERSION & BRANDING
# ====================================================================================================

BOT_VERSION = "5.0.0"
BOT_NAME = "NEXUS PREMIUM BOT"
BOT_AUTHOR = "@VIP_DARK_GOD"
BOT_RELEASE_DATE = "2026-07-01"
BOT_COPYRIGHT = "© 2026 VIP DARK GOD. All Rights Reserved."
BOT_DESCRIPTION = "NEXUS Premium Like Bot - Send unlimited likes with Multi-API engine"

# ====================================================================================================
#                                               CONFIGURATION
# ====================================================================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7946266426:AAHo9m9fWsU7Fqf-p_LYnMKB6KrCMPV23u8")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable required")

# Default API (main)
DEFAULT_API_URL = "https://100-sandy.vercel.app/like"
DEFAULT_API_KEY = "PRIYANKS"
DEFAULT_API_NAME = "main"

DATA_FILE = "bot_data.json"
LOG_FILE = "bot.log"
ERROR_LOG_FILE = "error_log.txt"

OWNER_ID = int(os.environ.get("OWNER_ID", "7702588711"))
OWNER_USERNAME = "@VIP_DARK_GOD"
OWNER_CONTACT = "https://t.me/VIP_DARK_GOD"
OWNER_NAME = "VIP DARK GOD"
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "7702588711,8526073588").split(",")]

DAILY_LIKE_TIME = "04:00"
TIMEZONE = "Asia/Kolkata"
IST = ZoneInfo(TIMEZONE)

API_TIMEOUT = 30
API_MAX_RETRIES = 3
API_RETRY_DELAY = 5

# ====================================================================================================
#                                               LIMITS
# ====================================================================================================

NORMAL_USER_DAILY_LIMIT = 3
VIP_USER_DAILY_LIMIT = 5
MAX_AUTO_LIKE_DAYS = 365
MIN_AUTO_LIKE_DAYS = 1
COMMAND_COOLDOWN = 2

# ====================================================================================================
#                                               REGIONS
# ====================================================================================================

SUPPORTED_REGIONS = ["ind", "bd"]
REGION_NAMES = {"ind": "INDIA", "bd": "BANGLADESH"}
REGION_FLAGS = {"ind": "🇮🇳", "bd": "🇧🇩"}

# ====================================================================================================
#                                               LOGGING
# ====================================================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8') if os.access('.', os.W_OK) else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ====================================================================================================
#                                               GLOBALS
# ====================================================================================================

application = None
scheduler = None
bot_start_time = datetime.now(IST)
command_cooldowns = defaultdict(dict)
pending_verifications = {}

# ====================================================================================================
#                                               HELPERS
# ====================================================================================================

def is_owner(user_id) -> bool:
    try:
        return int(user_id) == OWNER_ID
    except:
        return False

def is_admin(user_id) -> bool:
    if is_owner(user_id):
        return True
    try:
        return int(user_id) in ADMIN_IDS
    except:
        return False

def is_admin_or_vip(user_id) -> bool:
    return is_admin(user_id) or is_vip(user_id)

def load_data() -> Dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure all keys exist
                if "multi_api" not in data:
                    data["multi_api"] = {"apis": {}, "default_api": DEFAULT_API_NAME}
                if "allowed_groups" not in data:
                    data["allowed_groups"] = []
                if "verify_requirements" not in data:
                    data["verify_requirements"] = {}
                if "verified_users" not in data:
                    data["verified_users"] = {}
                if "verify_settings" not in data:
                    data["verify_settings"] = {"enabled": False}
                if "vip_users" not in data:
                    data["vip_users"] = {}
                if "auto_like_uids" not in data:
                    data["auto_like_uids"] = {}
                if "total_likes" not in data:
                    data["total_likes"] = {}
                if "daily_like_tracker" not in data:
                    data["daily_like_tracker"] = {}
                if "api_stats" not in data:
                    data["api_stats"] = {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
                if "users" not in data:
                    data["users"] = {}
                if "total_likes_sent" not in data:
                    data["total_likes_sent"] = 0
                if "total_auto_likes_sent" not in data:
                    data["total_auto_likes_sent"] = 0
                return data
        except:
            return initialize_data()
    return initialize_data()

def initialize_data() -> Dict:
    return {
        "users": {},
        "total_likes": {},
        "allowed_groups": [],
        "auto_like_uids": {},
        "settings": {
            "daily_like_time": DAILY_LIKE_TIME,
            "auto_like_enabled": True
        },
        "api_stats": {
            "total_calls": 0, "successful_calls": 0, "failed_calls": 0,
            "response_times": []
        },
        "vip_users": {},
        "daily_like_tracker": {},
        "verified_users": {},
        "verify_requirements": {},
        "verify_settings": {"enabled": False},
        "multi_api": {
            "apis": {},
            "default_api": DEFAULT_API_NAME
        },
        "total_likes_sent": 0,
        "total_auto_likes_sent": 0,
        "bot_start_time": datetime.now(IST).isoformat()
    }

def save_data(data: Dict) -> bool:
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp:
            json.dump(data, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
        shutil.move(tmp.name, DATA_FILE)
        return True
    except Exception as e:
        logger.error(f"Save error: {e}")
        return False

def update_user_info(data: Dict, user) -> Dict:
    uid = str(user.id)
    name = user.first_name or ""
    if user.last_name:
        name += f" {user.last_name}"
    username = user.username or "N/A"
    if uid not in data["users"]:
        data["users"][uid] = {
            "telegram_name": name, "username": username,
            "first_seen": datetime.now(IST).isoformat(),
            "last_seen": datetime.now(IST).isoformat(),
            "total_commands": 1, "likes_sent": 0
        }
    else:
        data["users"][uid]["last_seen"] = datetime.now(IST).isoformat()
        data["users"][uid]["total_commands"] = data["users"][uid].get("total_commands", 0) + 1
    return data

def is_vip(user_id) -> bool:
    if is_owner(user_id):
        return True
    data = load_data()
    uid = str(user_id)
    if uid in data.get("vip_users", {}):
        try:
            exp = datetime.fromisoformat(data["vip_users"][uid]["expiry"]).astimezone(IST)
            if exp > datetime.now(IST):
                return True
            del data["vip_users"][uid]
            save_data(data)
        except:
            pass
    return False

def get_daily_limit(user_id) -> Union[int, float]:
    if is_owner(user_id):
        return float('inf')
    if is_vip(user_id):
        return VIP_USER_DAILY_LIMIT
    return NORMAL_USER_DAILY_LIMIT

def can_send_like_today(user_id, uid: str, region: str) -> Tuple[bool, int]:
    if is_owner(user_id):
        return True, 999999
    data = load_data()
    today = datetime.now(IST).strftime("%Y-%m-%d")
    key = f"{user_id}_{uid}_{region}_{today}"
    count = data.get("daily_like_tracker", {}).get(key, 0)
    limit = get_daily_limit(user_id)
    return count < limit, limit

def increment_daily_counter(user_id, uid: str, region: str):
    if is_owner(user_id):
        return
    data = load_data()
    today = datetime.now(IST).strftime("%Y-%m-%d")
    key = f"{user_id}_{uid}_{region}_{today}"
    if "daily_like_tracker" not in data:
        data["daily_like_tracker"] = {}
    data["daily_like_tracker"][key] = data["daily_like_tracker"].get(key, 0) + 1
    save_data(data)

def get_uptime() -> str:
    diff = datetime.now(IST) - bot_start_time
    d = diff.days
    h = diff.seconds // 3600
    m = (diff.seconds % 3600) // 60
    s = diff.seconds % 60
    return f"{d}d {h}h {m}m {s}s"

def get_formatted_time() -> str:
    return datetime.now(IST).strftime('%I:%M:%S %p').lstrip('0') + f" {datetime.now(IST).strftime('%Z')}"

def check_cooldown(user_id: int, cmd: str, sec: int = 2) -> bool:
    now = time.time()
    if user_id in command_cooldowns and cmd in command_cooldowns[user_id]:
        if now - command_cooldowns[user_id][cmd] < sec:
            return True
    command_cooldowns[user_id][cmd] = now
    return False

# ====================================================================================================
#                                               MULTI-API SYSTEM
# ====================================================================================================

def get_active_apis() -> Dict:
    """Get all active APIs including default"""
    data = load_data()
    apis = data.get("multi_api", {}).get("apis", {})
    default_name = data.get("multi_api", {}).get("default_api", DEFAULT_API_NAME)
    
    # Always include default API
    result = {
        DEFAULT_API_NAME: {
            "url": DEFAULT_API_URL,
            "key": DEFAULT_API_KEY,
            "name": DEFAULT_API_NAME,
            "enabled": True,
            "is_default": True
        }
    }
    
    # Add custom APIs
    for name, api in apis.items():
        if api.get("enabled", True):
            result[name] = api
            result[name]["is_default"] = False
    
    return result

async def call_api(uid: str, region: str, api_name: str = None) -> Dict:
    """Call a specific API or all APIs and return combined result"""
    apis = get_active_apis()
    
    if api_name and api_name in apis:
        # Call specific API
        api = apis[api_name]
        return await call_single_api(uid, region, api["url"], api["key"])
    
    # Call all enabled APIs and combine
    best_result = {"LikesGivenByAPI": 0, "status": "error"}
    for name, api in apis.items():
        try:
            result = await call_single_api(uid, region, api["url"], api["key"])
            if result.get("LikesGivenByAPI", 0) > best_result.get("LikesGivenByAPI", 0):
                best_result = result
                best_result["api_used"] = name
        except:
            continue
    
    return best_result

async def call_single_api(uid: str, region: str, api_url: str, api_key: str) -> Dict:
    """Call a single API endpoint"""
    url = f"{api_url}?uid={uid}&server_name={region.lower()}&key={api_key}"
    start = time.time()
    
    try:
        logger.info(f"📡 Calling API: {api_url} for UID: {uid}")
        resp = requests.get(url, timeout=API_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        rt = time.time() - start
        
        # Update stats
        stats = load_data()["api_stats"]
        stats["total_calls"] = stats.get("total_calls", 0) + 1
        if data.get("LikesGivenByAPI", 0) > 0:
            stats["successful_calls"] = stats.get("successful_calls", 0) + 1
        else:
            stats["failed_calls"] = stats.get("failed_calls", 0) + 1
        stats["response_times"] = (stats.get("response_times", []) + [rt])[-100:]
        if stats["response_times"]:
            stats["average_response_time"] = sum(stats["response_times"]) / len(stats["response_times"])
        
        return data
    except Exception as e:
        logger.error(f"API error: {e}")
        return {"LikesGivenByAPI": 0, "status": "error", "error": str(e)}

# ====================================================================================================
#                                               MULTI-API COMMANDS
# ====================================================================================================

async def addapi_command(update: Update, context):
    """Add a custom API - /addapi name url key"""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    if len(context.args) < 3:
        await update.message.reply_text(
            "📝 Usage:\n/addapi <name> <url> <key>\n\n"
            "Example:\n/addapi myapi https://example.com/like mykey123"
        )
        return
    name = context.args[0]
    url = context.args[1]
    key = context.args[2]
    
    data = load_data()
    if "multi_api" not in data:
        data["multi_api"] = {"apis": {}, "default_api": DEFAULT_API_NAME}
    if name in data["multi_api"]["apis"]:
        await update.message.reply_text(f"❌ API '{name}' already exists! Use /removeapi first.")
        return
    
    data["multi_api"]["apis"][name] = {
        "url": url,
        "key": key,
        "enabled": True,
        "added_by": str(update.effective_user.id),
        "added_on": datetime.now(IST).isoformat()
    }
    save_data(data)
    await update.message.reply_text(
        f"✅ API '{name}' added successfully!\n\n"
        f"URL: {url}\n"
        f"Key: {key[:10]}...\n"
        f"Status: ✅ Enabled"
    )

async def removeapi_command(update: Update, context):
    """Remove a custom API - /removeapi name"""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    if not context.args:
        await update.message.reply_text("Usage: /removeapi <name>")
        return
    name = context.args[0]
    if name == DEFAULT_API_NAME:
        await update.message.reply_text("❌ Cannot remove default API!")
        return
    
    data = load_data()
    if name in data.get("multi_api", {}).get("apis", {}):
        del data["multi_api"]["apis"][name]
        save_data(data)
        await update.message.reply_text(f"✅ API '{name}' removed!")
    else:
        await update.message.reply_text(f"❌ API '{name}' not found!")

async def listapi_command(update: Update, context):
    """List all APIs"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    apis = get_active_apis()
    msg = "╔══════════════════════════════════════════╗\n"
    msg += "║         🔌 MULTI-API SYSTEM             ║\n"
    msg += "╚══════════════════════════════════════════╝\n\n"
    
    for name, api in apis.items():
        default = "⭐ DEFAULT" if api.get("is_default") else ""
        status = "✅" if api.get("enabled", True) else "❌"
        key_preview = "******"
        msg += f"{status} **{name}** {default}\n"
        msg += f"   URL: {api.get('url', 'N/A')[:50]}\n"
        msg += f"   Key: {key_preview}\n\n"
    
    data = load_data()
    custom_count = len(data.get("multi_api", {}).get("apis", {}))
    msg += f"📊 Custom APIs: {custom_count}\n"
    msg += f"📝 /addapi <name> <url> <key> - Add API\n"
    msg += f"🗑 /removeapi <name> - Remove API"
    
    await update.message.reply_text(msg)

async def toggleapi_command(update: Update, context):
    """Enable/disable a custom API"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    if not context.args:
        await update.message.reply_text("Usage: /toggleapi <name>")
        return
    name = context.args[0]
    if name == DEFAULT_API_NAME:
        await update.message.reply_text("❌ Cannot disable default API!")
        return
    
    data = load_data()
    if name in data.get("multi_api", {}).get("apis", {}):
        current = data["multi_api"]["apis"][name].get("enabled", True)
        data["multi_api"]["apis"][name]["enabled"] = not current
        save_data(data)
        status = "✅ Enabled" if not current else "❌ Disabled"
        await update.message.reply_text(f"✅ API '{name}' {status}!")
    else:
        await update.message.reply_text(f"❌ API '{name}' not found!")

# ====================================================================================================
#                                               GROUP MANAGEMENT
# ====================================================================================================

async def addgroup_command(update: Update, context):
    """Add a group to allowed list - /addgroup [-100123456789]"""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    
    # Check if replied to a message in a group
    chat = update.effective_chat
    chat_id = str(chat.id)
    chat_title = chat.title or "Unknown Group"
    
    if chat.type in ["group", "supergroup"]:
        # Adding current group
        data = load_data()
        if "allowed_groups" not in data:
            data["allowed_groups"] = []
        
        # Check if already added
        for g in data["allowed_groups"]:
            if g.get("id") == chat_id:
                await update.message.reply_text(f"✅ Group '{chat_title}' is already allowed!")
                return
        
        data["allowed_groups"].append({
            "id": chat_id,
            "title": chat_title,
            "added_by": str(update.effective_user.id),
            "added_on": datetime.now(IST).isoformat()
        })
        save_data(data)
        await update.message.reply_text(
            f"✅ Group '{chat_title}' added to allowed list!\n"
            f"ID: {chat_id}"
        )
    elif context.args:
        # Adding by ID
        group_id = context.args[0]
        group_name = " ".join(context.args[1:]) if len(context.args) > 1 else group_id
        data = load_data()
        if "allowed_groups" not in data:
            data["allowed_groups"] = []
        for g in data["allowed_groups"]:
            if g.get("id") == group_id:
                await update.message.reply_text(f"✅ Group {group_id} already allowed!")
                return
        data["allowed_groups"].append({
            "id": group_id,
            "title": group_name,
            "added_by": str(update.effective_user.id),
            "added_on": datetime.now(IST).isoformat()
        })
        save_data(data)
        await update.message.reply_text(f"✅ Group {group_name} ({group_id}) added!")
    else:
        await update.message.reply_text(
            "📝 Usage:\n"
            "1. Send this command in the group to add it\n"
            "2. Or: /addgroup <group_id> [group_name]"
        )

async def removegroup_command(update: Update, context):
    """Remove a group from allowed list"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    data = load_data()
    allowed = data.get("allowed_groups", [])
    
    if not context.args and update.effective_chat.type in ["group", "supergroup"]:
        # Remove current group
        chat_id = str(update.effective_chat.id)
        found = [g for g in allowed if g.get("id") == chat_id]
        if found:
            data["allowed_groups"] = [g for g in allowed if g.get("id") != chat_id]
            save_data(data)
            await update.message.reply_text(f"✅ Group removed from allowed list!")
        else:
            await update.message.reply_text("❌ This group is not in allowed list!")
    elif context.args:
        group_id = context.args[0]
        found = [g for g in allowed if g.get("id") == group_id]
        if found:
            data["allowed_groups"] = [g for g in allowed if g.get("id") != group_id]
            save_data(data)
            await update.message.reply_text(f"✅ Group {group_id} removed!")
        else:
            await update.message.reply_text(f"❌ Group {group_id} not found!")
    else:
        await update.message.reply_text("Usage: /removegroup <group_id>")

async def listgroups_command(update: Update, context):
    """List all allowed groups"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    data = load_data()
    allowed = data.get("allowed_groups", [])
    
    if not allowed:
        await update.message.reply_text("📋 No groups in allowed list.\nAdd one: /addgroup in the group chat")
        return
    
    msg = "╔══════════════════════════════════════════╗\n"
    msg += "║         👥 ALLOWED GROUPS                ║\n"
    msg += "╚══════════════════════════════════════════╝\n\n"
    
    for i, g in enumerate(allowed, 1):
        msg += f"{i}. {g.get('title', 'Unknown')}\n"
        msg += f"   ID: {g.get('id', 'N/A')}\n"
        msg += f"   Added: {g.get('added_on', 'N/A')[:10]}\n\n"
    
    await update.message.reply_text(msg)

# ====================================================================================================
#                                               VERIFICATION SYSTEM
# ====================================================================================================

async def check_verification(user_id: int) -> Tuple[bool, Optional[str]]:
    data = load_data()
    uid = str(user_id)
    if is_owner(user_id) or is_vip(user_id):
        return True, None
    if not data.get("verify_settings", {}).get("enabled", False):
        return True, None
    if uid in data.get("verified_users", {}):
        return True, None
    for channel, req in data.get("verify_requirements", {}).items():
        if req.get("enabled", True):
            return False, channel
    return True, None

async def send_verification_message(update: Update, context, channel: str, cmd: str = None):
    user = update.effective_user
    data = load_data()
    btn_text = data.get("verify_requirements", {}).get(channel, {}).get("button_text", "🔗 Join Channel")
    
    keyboard = [
        [InlineKeyboardButton(btn_text, url=f"https://t.me/{channel.replace('@', '')}")],
        [InlineKeyboardButton("✅ Check Verification", callback_data=f"verify_{user.id}_{channel}")]
    ]
    pending_verifications[str(user.id)] = {"channel": channel, "time": time.time(), "cmd": cmd}
    
    await update.message.reply_text(
        f"🔐 **Verification Required!**\n\n"
        f"Hey {user.first_name}! 👋\n\n"
        f"To use this bot, join our channel first:\n📢 {channel}\n\n"
        f"After joining, click 'Check Verification' ✅\n\n"
        f"💎 Powered by VIP DARK GOD",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def verify_callback(update: Update, context):
    q = update.callback_query
    await q.answer()
    data = q.data
    
    if data.startswith("verify_"):
        parts = data.split("_")
        if len(parts) >= 3:
            uid = int(parts[1])
            channel = parts[2]
            
            if q.from_user.id != uid:
                await q.edit_message_text("❌ This button is not for you!", reply_markup=None)
                return
            
            try:
                member = await context.bot.get_chat_member(f"@{channel.replace('@', '')}", uid)
                if member.status in ["member", "administrator", "creator"]:
                    db = load_data()
                    db["verified_users"][str(uid)] = {
                        "verified_at": datetime.now(IST).isoformat(),
                        "channel": channel
                    }
                    save_data(db)
                    if str(uid) in pending_verifications:
                        del pending_verifications[str(uid)]
                    
                    await q.edit_message_text(
                        f"✅ **Verification Successful!**\n\n"
                        f"Congratulations {q.from_user.first_name}! 🎉\n\n"
                        f"Now you can use the bot to send likes!\n"
                        f"Try /like ind UID or /like bd UID\n\n"
                        f"💎 Powered by VIP DARK GOD",
                        reply_markup=None
                    )
                else:
                    await q.edit_message_text(
                        f"❌ You haven't joined {channel} yet!\n"
                        f"Please join first, then click check again.\n\n"
                        f"Join: https://t.me/{channel.replace('@', '')}",
                        reply_markup=None
                    )
            except Exception as e:
                await q.edit_message_text(
                    f"❌ Error checking verification!\n"
                    f"Make sure you joined the channel and try again.\n"
                    f"Error: {str(e)[:50]}",
                    reply_markup=None
                )

async def addverify_command(update: Update, context):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addverify @channel Button Text")
        return
    channel = context.args[0]
    if not channel.startswith("@"):
        channel = f"@{channel}"
    btn = " ".join(context.args[1:])
    
    data = load_data()
    data["verify_requirements"][channel] = {
        "button_text": btn, "enabled": True,
        "added_by": str(update.effective_user.id),
        "added_on": datetime.now(IST).isoformat()
    }
    data["verify_settings"]["enabled"] = True
    save_data(data)
    await update.message.reply_text(f"✅ Verification requirement added!\nChannel: {channel}\nButton: {btn}")

async def removeverify_command(update: Update, context):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    if not context.args:
        await update.message.reply_text("Usage: /removeverify @channel")
        return
    channel = context.args[0]
    if not channel.startswith("@"):
        channel = f"@{channel}"
    data = load_data()
    if channel in data.get("verify_requirements", {}):
        del data["verify_requirements"][channel]
        save_data(data)
        await update.message.reply_text(f"✅ Verification removed for {channel}")
    else:
        await update.message.reply_text(f"❌ Not found: {channel}")

async def toggleverify_command(update: Update, context):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    data = load_data()
    current = data.get("verify_settings", {}).get("enabled", False)
    data["verify_settings"]["enabled"] = not current
    save_data(data)
    s = "✅ Enabled" if not current else "❌ Disabled"
    await update.message.reply_text(f"Verification {s}!")

# ====================================================================================================
#                                               LIKE COMMAND
# ====================================================================================================

async def like_command(update: Update, context):
    user_id = update.effective_user.id
    
    # Check verification
    if not is_owner(user_id) and not is_vip(user_id):
        ok, ch = await check_verification(user_id)
        if not ok and ch:
            await send_verification_message(update, context, ch, "like")
            return
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ **Usage:** /like <region> <UID>\n\n"
            "Example:\n/like ind 3092970870\n/like bd 10609031393\n\n"
            "💎 Powered by VIP DARK GOD"
        )
        return
    
    region = context.args[0].lower()
    uid = context.args[1]
    
    if region not in SUPPORTED_REGIONS:
        await update.message.reply_text(f"❌ Invalid region! Use: ind or bd")
        return
    if not uid.isdigit() or len(uid) < 8 or len(uid) > 15:
        await update.message.reply_text("❌ Invalid UID! Must be 8-15 digits")
        return
    
    ok, limit = can_send_like_today(str(user_id), uid, region)
    if not ok:
        await update.message.reply_text(f"❌ Daily limit reached! Limit: {limit}/day")
        return
    
    # Processing
    msg = await update.message.reply_text("⏳ Processing your request...")
    
    # Call API (uses multi-api system)
    result = await call_api(uid, region)
    likes = result.get("LikesGivenByAPI", 0)
    
    try:
        await msg.delete()
    except:
        pass
    
    if likes > 0:
        increment_daily_counter(str(user_id), uid, region)
        data = load_data()
        data["total_likes_sent"] = data.get("total_likes_sent", 0) + likes
        if str(user_id) not in data["total_likes"]:
            data["total_likes"][str(user_id)] = {"count": 0, "days": 0}
        data["total_likes"][str(user_id)]["count"] += likes
        data["total_likes"][str(user_id)]["days"] += 1
        save_data(data)
        
        player = result.get("PlayerNickname", "N/A")
        before = result.get("LikesbeforeCommand", "N/A")
        after = result.get("LikesafterCommand", "N/A")
        api_used = result.get("api_used", "default")
        flag = REGION_FLAGS.get(region, "🌍")
        
        await update.message.reply_text(
            f"✅ **LIKES SENT SUCCESSFULLY!**\n\n"
            f"👤 Player: {player}\n"
            f"🎮 UID: {uid}\n"
            f"🌍 Region: {region.upper()} {flag}\n"
            f"💖 Before: {before}\n"
            f"✨ Given: +{likes}\n"
            f"💫 After: {after}\n"
            f"🔌 API: {api_used}\n"
            f"⏰ Time: {get_formatted_time()}\n\n"
            f"💎 Powered by VIP DARK GOD"
        )
    else:
        await update.message.reply_text(
            f"❌ **LIKES FAILED!**\n\n"
            f"🎮 UID: {uid}\n"
            f"🌍 Region: {region.upper()}\n"
            f"⚠️ Please try again later.\n\n"
            f"💎 Powered by VIP DARK GOD"
        )

# ====================================================================================================
#                                               VIP MANAGEMENT
# ====================================================================================================

async def addvip_command(update: Update, context):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /addvip <user_id> [days]")
        return
    target = context.args[0]
    days = int(context.args[1]) if len(context.args) > 1 else 30
    if days < 1 or days > 365:
        await update.message.reply_text("❌ Days must be 1-365")
        return
    if int(target) == OWNER_ID:
        await update.message.reply_text("❌ Owner is already unlimited!")
        return
    
    data = load_data()
    exp = (datetime.now(IST) + timedelta(days=days)).isoformat()
    
    if target in data.get("vip_users", {}):
        old = datetime.fromisoformat(data["vip_users"][target]["expiry"]).astimezone(IST)
        new_exp = old + timedelta(days=days)
        data["vip_users"][target]["expiry"] = new_exp.isoformat()
        data["vip_users"][target]["days"] = data["vip_users"][target].get("days", 0) + days
        action = "Extended"
        exp_display = new_exp.strftime('%Y-%m-%d %H:%M')
    else:
        data["vip_users"][target] = {
            "expiry": exp, "days": days,
            "added_by": str(update.effective_user.id),
            "added_on": datetime.now(IST).isoformat()
        }
        action = "Added"
        exp_display = datetime.fromisoformat(exp).strftime('%Y-%m-%d %H:%M')
    
    save_data(data)
    await update.message.reply_text(
        f"✅ VIP {action} for user {target}!\n"
        f"Days: {days}\n"
        f"Expiry: {exp_display}\n"
        f"Limit: 5 likes/day"
    )
    try:
        await application.bot.send_message(
            chat_id=int(target),
            text=f"🎉 **VIP Status Granted!**\n\n"
                 f"Days: {days}\nExpiry: {exp_display}\n"
                 f"Limit: 5 likes/day\n\n"
                 f"💎 Powered by VIP DARK GOD"
        )
    except:
        pass

async def removevip_command(update: Update, context):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    if not context.args:
        await update.message.reply_text("Usage: /removevip <user_id>")
        return
    target = context.args[0]
    data = load_data()
    if target in data.get("vip_users", {}):
        del data["vip_users"][target]
        save_data(data)
        await update.message.reply_text(f"✅ VIP removed from {target}")
    else:
        await update.message.reply_text(f"❌ User {target} is not VIP")

async def listvip_command(update: Update, context):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    data = load_data()
    vips = data.get("vip_users", {})
    if not vips:
        await update.message.reply_text("📋 No VIP users yet.")
        return
    msg = "╔══════════════════════════════════════════╗\n"
    msg += "║           👑 VIP USERS LIST              ║\n"
    msg += "╚══════════════════════════════════════════╝\n\n"
    for uid, info in vips.items():
        try:
            exp = datetime.fromisoformat(info["expiry"]).astimezone(IST)
            left = max(0, (exp - datetime.now(IST)).days)
            msg += f"👤 ID: {uid}\n  📅 Left: {left}d\n  📊 Limit: 5/day\n\n"
        except:
            pass
    await update.message.reply_text(msg)

# ====================================================================================================
#                                               AUTO-LIKE
# ====================================================================================================

async def autolike_command(update: Update, context):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    
    if len(context.args) == 3:
        uid = context.args[0]
        region = context.args[1].lower()
        try:
            days = int(context.args[2])
        except:
            await update.message.reply_text("❌ Invalid days!")
            return
        target = str(OWNER_ID)
    elif len(context.args) == 4:
        uid = context.args[0]
        region = context.args[1].lower()
        try:
            days = int(context.args[2])
        except:
            await update.message.reply_text("❌ Invalid days!")
            return
        target = context.args[3]
    else:
        await update.message.reply_text(
            "Usage:\n"
            "/autolike <uid> <region> <days> - for yourself\n"
            "/autolike <uid> <region> <days> <user_id> - for another user"
        )
        return
    
    if region not in SUPPORTED_REGIONS:
        await update.message.reply_text("❌ Invalid region! Use ind or bd")
        return
    if days < 1 or days > 365:
        await update.message.reply_text("❌ Days must be 1-365")
        return
    
    data = load_data()
    exp = (datetime.now(IST) + timedelta(days=days)).isoformat()
    key = f"{target}_{uid}"
    
    if key in data.get("auto_like_uids", {}):
        old = datetime.fromisoformat(data["auto_like_uids"][key]["expiry_date"]).astimezone(IST)
        new_exp = old + timedelta(days=days)
        data["auto_like_uids"][key]["expiry_date"] = new_exp.isoformat()
        data["auto_like_uids"][key]["days"] = data["auto_like_uids"][key].get("days", 0) + days
        action = "Extended"
        exp_display = new_exp.strftime('%Y-%m-%d %H:%M')
    else:
        data["auto_like_uids"][key] = {
            "uid": uid, "region": region,
            "expiry_date": exp, "user_id": target,
            "days": days, "created_at": datetime.now(IST).isoformat(),
            "total_likes": 0
        }
        action = "Created"
        exp_display = datetime.fromisoformat(exp).strftime('%Y-%m-%d %H:%M')
    
    save_data(data)
    await update.message.reply_text(
        f"✅ Auto-like {action}!\n"
        f"UID: {uid}\nRegion: {region.upper()}\n"
        f"Days: {days}\nExpiry: {exp_display}\n"
        f"User: {target}"
    )

# ====================================================================================================
#                                               USER COMMANDS
# ====================================================================================================

async def start_command(update: Update, context):
    user = update.effective_user
    data = load_data()
    data = update_user_info(data, user)
    save_data(data)
    uid = user.id
    
    if is_owner(uid) or is_admin(uid):
        await update.message.reply_text(
            f"╔══════════════════════════════════════════╗\n"
            f"║        🔑 NEXUS OWNER PANEL 🔑           ║\n"
            f"╚══════════════════════════════════════════╝\n\n"
            f"Welcome Boss, {user.first_name}! 🎯\n\n"
            f"**Commands:**\n"
            f"/like <region> <UID> - Send likes\n"
            f"/addapi <name> <url> <key> - Add API\n"
            f"/removeapi <name> - Remove API\n"
            f"/listapi - List all APIs\n"
            f"/toggleapi <name> - Enable/Disable API\n"
            f"/addgroup - Add current group\n"
            f"/removegroup - Remove group\n"
            f"/listgroups - List allowed groups\n"
            f"/addvip <id> [days] - Add VIP\n"
            f"/removevip <id> - Remove VIP\n"
            f"/listvip - List VIP users\n"
            f"/autolike <uid> <reg> <days> - Auto-like\n"
            f"/addverify @channel text - Add verify\n"
            f"/removeverify @channel - Remove verify\n"
            f"/toggleverify - On/Off verification\n"
            f"/mylikes - Your total likes\n"
            f"/myuids - Your auto-like UIDs\n"
            f"/vipstatus - Your VIP status\n"
            f"/status - Bot statistics\n"
            f"/runnow - Run auto-like now\n"
            f"/resetdaily - Reset counters\n\n"
            f"💎 Powered by VIP DARK GOD"
        )
    else:
        ok, ch = await check_verification(uid)
        if not ok and ch:
            await send_verification_message(update, context, ch, "start")
            return
        
        limit = get_daily_limit(uid)
        limit_s = "∞" if limit == float('inf') else str(limit)
        status = "👑 Owner" if is_owner(uid) else "⭐ VIP" if is_vip(uid) else "🟢 User"
        
        await update.message.reply_text(
            f"╔══════════════════════════════════════════╗\n"
            f"║        🤖 NEXUS LIKE BOT 🤖              ║\n"
            f"╚══════════════════════════════════════════╝\n\n"
            f"Hello {user.first_name}! 👋\n\n"
            f"**Your Status:** {status}\n"
            f"**Daily Limit:** {limit_s}/day\n\n"
            f"**Available Commands:**\n"
            f"/like <region> <UID> - Send likes\n"
            f"/mylikes - Your total likes\n"
            f"/myuids - Your auto-like UIDs\n"
            f"/vipstatus - Check VIP status\n\n"
            f"**Example:** /like ind 3092970870\n\n"
            f"💎 Powered by VIP DARK GOD"
        )

async def mylikes_command(update: Update, context):
    uid = update.effective_user.id
    data = load_data()
    likes = data.get("total_likes", {}).get(str(uid), {}).get("count", 0)
    days = data.get("total_likes", {}).get(str(uid), {}).get("days", 0)
    await update.message.reply_text(
        f"📊 **Your Likes Summary**\n\n"
        f"❤️ Total Likes: {likes}\n"
        f"📅 Total Days: {days}\n"
        f"📊 Daily Limit: {get_daily_limit(uid)}\n\n"
        f"💎 Powered by VIP DARK GOD"
    )

async def myuids_command(update: Update, context):
    uid = update.effective_user.id
    data = load_data()
    auto = data.get("auto_like_uids", {})
    user_uids = [(k, v) for k, v in auto.items() if v.get("user_id") == str(uid)]
    
    if not user_uids:
        await update.message.reply_text(
            f"📭 **No auto-like UIDs found.**\n\n"
            f"💎 Powered by VIP DARK GOD"
        )
        return
    
    msg = "╔══════════════════════════════════════════╗\n"
    msg += "║        📋 YOUR AUTO-LIKE UIDs            ║\n"
    msg += "╚══════════════════════════════════════════╝\n\n"
    
    for i, (key, info) in enumerate(user_uids[:10], 1):
        exp = datetime.fromisoformat(info["expiry_date"]).astimezone(IST)
        left = max(0, (exp - datetime.now(IST)).days)
        msg += f"**#{i}** `{info['uid']}`\n"
        msg += f"   Region: {info['region'].upper()} | Left: {left}d\n\n"
    
    await update.message.reply_text(msg)

async def vipstatus_command(update: Update, context):
    uid = update.effective_user.id
    if is_owner(uid) or is_admin(uid):
        await update.message.reply_text("👑 **Owner** - Unlimited access!")
    elif is_vip(uid):
        data = load_data()
        exp = datetime.fromisoformat(data["vip_users"][str(uid)]["expiry"]).astimezone(IST)
        left = max(0, (exp - datetime.now(IST)).days)
        await update.message.reply_text(
            f"⭐ **VIP Active** ✅\n"
            f"Days Left: {left}\n"
            f"Limit: 5 likes/day\n"
            f"Expiry: {exp.strftime('%Y-%m-%d')}\n\n"
            f"💎 Powered by VIP DARK GOD"
        )
    else:
        await update.message.reply_text(
            f"🟢 **Normal User**\n"
            f"Limit: 3 likes/day\n\n"
            f"Want VIP? Contact @VIP_DARK_GOD\n\n"
            f"💎 Powered by VIP DARK GOD"
        )

# ====================================================================================================
#                                               OWNER UTILITIES
# ====================================================================================================

async def status_command(update: Update, context):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    data = load_data()
    users = len(data.get("users", {}))
    vips = len(data.get("vip_users", {}))
    auto = len(data.get("auto_like_uids", {}))
    api_stats = data.get("api_stats", {})
    total = data.get("total_likes_sent", 0)
    verified = len(data.get("verified_users", {}))
    groups = len(data.get("allowed_groups", []))
    custom_apis = len(data.get("multi_api", {}).get("apis", {}))
    
    msg = f"╔══════════════════════════════════════════╗\n"
    msg += f"║        📊 NEXUS BOT STATS 📊            ║\n"
    msg += f"╚══════════════════════════════════════════╝\n\n"
    msg += f"**Users:** {users} | **VIP:** {vips}\n"
    msg += f"**Auto-Like UIDs:** {auto}\n"
    msg += f"**Total Likes Sent:** {total}\n"
    msg += f"**Verified Users:** {verified}\n"
    msg += f"**Allowed Groups:** {groups}\n"
    msg += f"**Custom APIs:** {custom_apis}\n\n"
    msg += f"**API Stats:**\n"
    msg += f"  Total Calls: {api_stats.get('total_calls', 0)}\n"
    msg += f"  Successful: {api_stats.get('successful_calls', 0)}\n"
    msg += f"  Failed: {api_stats.get('failed_calls', 0)}\n"
    msg += f"  Avg Response: {api_stats.get('average_response_time', 0):.2f}s\n\n"
    msg += f"**System:**\n"
    msg += f"  Uptime: {get_uptime()}\n"
    msg += f"  Version: {BOT_VERSION}\n"
    msg += f"  Daily Time: {DAILY_LIKE_TIME} IST\n\n"
    msg += f"💎 Powered by VIP DARK GOD"
    
    await update.message.reply_text(msg)

async def runnow_command(update: Update, context):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    msg = await update.message.reply_text("⏳ Running daily auto-like job...")
    try:
        await daily_job()
        await msg.edit_text("✅ Auto-like job completed!")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

async def resetdaily_command(update: Update, context):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    reset_daily_counters()
    await update.message.reply_text("✅ Daily counters reset!")

# ====================================================================================================
#                                               DAILY AUTO-LIKE JOB
# ====================================================================================================

async def daily_job():
    logger.info("🚀 Starting daily auto-like job...")
    data = load_data()
    auto = data.get("auto_like_uids", {})
    
    if not auto:
        logger.info("No auto-like UIDs found.")
        return
    
    success = 0
    failed = 0
    expired = 0
    
    for key, info in list(auto.items()):
        uid = info.get("uid")
        region = info.get("region")
        user_id = info.get("user_id")
        
        if not user_id:
            continue
        
        # Check expiry
        try:
            exp = datetime.fromisoformat(info["expiry_date"]).astimezone(IST)
            if exp <= datetime.now(IST):
                del auto[key]
                data["auto_like_uids"] = auto
                save_data(data)
                expired += 1
                logger.info(f"Expired: {uid}")
                continue
        except:
            continue
        
        # Send like
        try:
            result = await call_api(uid, region)
            likes = result.get("LikesGivenByAPI", 0)
            if likes > 0:
                auto[key]["total_likes"] = auto[key].get("total_likes", 0) + likes
                auto[key]["last_run"] = datetime.now(IST).isoformat()
                data["total_auto_likes_sent"] = data.get("total_auto_likes_sent", 0) + likes
                data["auto_like_uids"] = auto
                save_data(data)
                success += 1
                logger.info(f"✅ Auto-like: {uid} → {likes}")
                
                # Notify user
                try:
                    await send_like_response(int(user_id), result, uid, region, True)
                except:
                    pass
            else:
                failed += 1
        except:
            failed += 1
        
        await asyncio.sleep(2)
    
    logger.info(f"Job done: {success} success, {failed} failed, {expired} expired")

async def send_like_response(chat_id: int, data: Dict, uid: str, region: str, is_auto: bool = False):
    likes = data.get("LikesGivenByAPI", 0)
    player = data.get("PlayerNickname", "N/A")
    flag = REGION_FLAGS.get(region, "🌍")
    
    if likes > 0:
        msg = f"✅ Auto-like sent!\n👤 {player}\n🎮 {uid}\n🌍 {region.upper()} {flag}\n❤️ +{likes}"
    else:
        msg = f"❌ Auto-like failed for {uid}"
    
    try:
        await application.bot.send_message(chat_id=chat_id, text=msg)
    except:
        pass

def reset_daily_counters():
    data = load_data()
    today = datetime.now(IST).strftime("%Y-%m-%d")
    dt = data.get("daily_like_tracker", {})
    data["daily_like_tracker"] = {k: v for k, v in dt.items() if k.endswith(today)}
    save_data(data)

# ====================================================================================================
#                                               RESCHEDULE
# ====================================================================================================

async def reschedule_jobs():
    global scheduler
    if scheduler:
        try:
            scheduler.remove_job("daily_job")
            scheduler.remove_job("reset_job")
        except:
            pass
        
        h, m = map(int, DAILY_LIKE_TIME.split(':'))
        scheduler.add_job(daily_job, CronTrigger(hour=h, minute=m, timezone=IST), id="daily_job")
        scheduler.add_job(reset_daily_counters, CronTrigger(hour=0, minute=0, timezone=IST), id="reset_job")

# ====================================================================================================
#                                               POST INIT
# ====================================================================================================

async def post_init(application: Application):
    global scheduler
    logger.info(f"🤖 Starting {BOT_NAME} v{BOT_VERSION}...")
    logger.info(f"👑 Owner: {OWNER_USERNAME}")
    
    scheduler = AsyncIOScheduler(timezone=IST)
    h, m = map(int, DAILY_LIKE_TIME.split(':'))
    scheduler.add_job(daily_job, CronTrigger(hour=h, minute=m, timezone=IST), id="daily_job")
    scheduler.add_job(reset_daily_counters, CronTrigger(hour=0, minute=0, timezone=IST), id="reset_job")
    scheduler.start()
    logger.info(f"✅ Scheduler started. Daily job at {DAILY_LIKE_TIME} IST")

# ====================================================================================================
#                                               MAIN
# ====================================================================================================

def main():
    global application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # User commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler(["help", "h"], start_command))
    application.add_handler(CommandHandler("like", like_command))
    application.add_handler(CommandHandler("mylikes", mylikes_command))
    application.add_handler(CommandHandler("myuids", myuids_command))
    application.add_handler(CommandHandler("vipstatus", vipstatus_command))
    
    # Owner utilities
    application.add_handler(CommandHandler("autolike", autolike_command))
    application.add_handler(CommandHandler("addvip", addvip_command))
    application.add_handler(CommandHandler("removevip", removevip_command))
    application.add_handler(CommandHandler("listvip", listvip_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("runnow", runnow_command))
    application.add_handler(CommandHandler("resetdaily", resetdaily_command))
    
    # Multi-API commands
    application.add_handler(CommandHandler("addapi", addapi_command))
    application.add_handler(CommandHandler("removeapi", removeapi_command))
    application.add_handler(CommandHandler("listapi", listapi_command))
    application.add_handler(CommandHandler("toggleapi", toggleapi_command))
    
    # Group management
    application.add_handler(CommandHandler("addgroup", addgroup_command))
    application.add_handler(CommandHandler("removegroup", removegroup_command))
    application.add_handler(CommandHandler("listgroups", listgroups_command))
    
    # Verification
    application.add_handler(CommandHandler("addverify", addverify_command))
    application.add_handler(CommandHandler("removeverify", removeverify_command))
    application.add_handler(CommandHandler("toggleverify", toggleverify_command))
    application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_"))
    
    application.post_init = post_init
    
    logger.info("🚀 Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
