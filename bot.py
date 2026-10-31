from flask import Flask
from threading import Thread
import sqlite3
import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "8968492791:AAEIN_xfHMvckTfXLLr9WRdlr3aaoUF-OCg"
CHANNEL = "https://t.me/motionscpmchannel"
CHANNEL_ID = "@motionscpmchannel"
GROUP = "https://t.me/motioncpmgroup"
GROUP_ID = "@motioncpmgroup"
OWNER = "https://t.me/MoxMotion"
BANNER = "AgACAgQAAxkBAAMOat-d6QzZfzBw3BR1xxaD9UseE1kAAl4RaxvB5YBSeGoaEuo12lABAAMCAAN5AAM9BA"
ADMIN_ID = 7774137350

# ---> PUT YOUR WEB APP LINKS HERE <---
CPM1_URL = "https://telegram-web-app-539x.bolt.host"
CPM2_URL = "https://telegram-web-app-539x.bolt.host" 

bot = telebot.TeleBot(TOKEN)

db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        banned INTEGER DEFAULT 0,
        join_date TEXT
    )
""")
db.commit()


def save_user(uid, name):
    today = datetime.date.today().isoformat()
    cur.execute("INSERT OR IGNORE INTO users (id, name, join_date) VALUES (?, ?, ?)", (uid, name, today))
    db.commit()


def is_banned(uid):
    cur.execute("SELECT banned FROM users WHERE id = ?", (uid,))
    row = cur.fetchone()
    return row and row[0] == 1

def is_joined(uid):
    try:
        a = bot.get_chat_member(CHANNEL_ID, uid)
        b = bot.get_chat_member(GROUP_ID, uid)
        ok = ["member", "administrator", "creator"]
        return a.status in ok and b.status in ok
    except Exception:
        return False


def gate_menu():
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL))
    kb.row(InlineKeyboardButton("👥 JOIN GROUP", url=GROUP))
    kb.row(InlineKeyboardButton("✅ VERIFY ACCESS", callback_data="verify"))
    return kb


def main_menu():
    kb = InlineKeyboardMarkup()
    
    # The big main button
    kb.row(InlineKeyboardButton("🚀 Open CPM Tool", web_app=WebAppInfo(url=CPM1_URL)))
    
    # The rest of the buttons
    kb.row(
        InlineKeyboardButton("📢 Join Channel", url=CHANNEL),
        InlineKeyboardButton("💬 Contact Owner", url=OWNER),
    )
    kb.row(
        InlineKeyboardButton("👥 Join Group", url=GROUP),
        InlineKeyboardButton("👤 Profile", callback_data="profile"),
    )
    kb.row(InlineKeyboardButton("🔄 Refresh Info", callback_data="refresh"))
    return kb


def gate_text(name):
    return (
        f"⚡ <b>CHANNEL + GROUP // ACCESS GATE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔒 <b>VERIFICATION</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📡 Join the official channel and group,\n"
        f"then press <b>VERIFY ACCESS</b>.\n\n"
        f"👋 Hello, <b>{name}</b> 🦅"
    )


def welcome_caption(name, uid):
    return (
        f"👋 Hello, <b>{name}</b> 🦅\n\n"
        f"⭐ <b>Your Information:</b>\n"
        f"🆔 Telegram ID: <code>{uid}</code>\n"
        f"👑 Role: <b>{'Admin' if uid == ADMIN_ID else 'User'}</b>\n\n"
        f"🚗 <b>CPM Services</b>\n"
        f"Click the button below to launch the Tool."
    )


@bot.message_handler(commands=["start"])
def start(msg):
    if is_banned(msg.from_user.id):
        return bot.reply_to(msg, "🚫 You are banned.")
    save_user(msg.from_user.id, msg.from_user.first_name or "friend")
    uid = msg.from_user.id
    name = msg.from_user.first_name or "friend"

    if is_joined(uid) or uid == ADMIN_ID:
        bot.send_photo(msg.chat.id, BANNER, caption=welcome_caption(name, uid),
                       parse_mode="HTML", reply_markup=main_menu())
    else:
        bot.send_photo(msg.chat.id, BANNER, caption=gate_text(name),
                       parse_mode="HTML", reply_markup=gate_menu())


@bot.message_handler(commands=["profile"])
def profile(msg):
    u = msg.from_user
    bot.reply_to(
        msg,
        f"👤 <b>Your Profile</b>\n\n"
        f"🆔 ID: <code>{u.id}</code>\n"
        f"👤 Name: <b>{u.first_name}</b>",
        parse_mode="HTML"
    )


@bot.message_handler(commands=["help"])
def help_cmd(msg):
    bot.reply_to(
        msg,
        "💬 <b>Help</b>\n\n"
        "🚀 /start — main menu\n"
        "👤 /profile — your info\n"
        "💬 /help — this message",
        parse_mode="HTML"
    )


@bot.message_handler(commands=["stats"])
def stats_cmd(msg):
    if msg.from_user.id != ADMIN_ID:
        return bot.reply_to(msg, "❌ Not allowed.")
    
    today = datetime.date.today().isoformat()
    
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM users WHERE join_date = ?", (today,))
    today_users = cur.fetchone()[0]
    
    cur.execute("SELECT name FROM users ORDER BY id DESC LIMIT 1")
    last_user_row = cur.fetchone()
    last_user = last_user_row[0] if last_user_row else "None"

    text = (
        f"📊 <b>Bot Statistics</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"📅 Joined Today: <b>{today_users}</b>\n"
        f"🕐 Last User: <b>{last_user}</b>"
    )
    bot.reply_to(msg, text, parse_mode="HTML")


@bot.message_handler(commands=["admin"])
def admin(msg):
    if msg.from_user.id != ADMIN_ID:
        return bot.reply_to(msg, "❌ Not allowed.")
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("👥 Users count", callback_data="a_count"),
        InlineKeyboardButton("📢 Broadcast", callback_data="a_broadcast"),
    )
    kb.row(
        InlineKeyboardButton("🚫 Ban", callback_data="a_ban"),
        InlineKeyboardButton("✅ Unban", callback_data="a_unban"),
    )
    kb.row(InlineKeyboardButton("📊 Stats", callback_data="a_stats"))
    bot.reply_to(msg, "🛠 <b>Admin Panel</b>", parse_mode="HTML", reply_markup=kb)


broadcast_state = set()


@bot.message_handler(func=lambda m: m.from_user.id in broadcast_state, content_types=["text"])
def do_broadcast(msg):
    broadcast_state.discard(msg.from_user.id)
    cur.execute("SELECT id FROM users")
    users = cur.fetchall()
    sent = 0
    for (uid,) in users:
        try:
            bot.send_message(uid, msg.text)
            sent += 1
        except Exception:
            pass
    bot.reply_to(msg, f"✅ Sent to {sent} users.")


@bot.message_handler(commands=["ban"])
def ban(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        uid = int(msg.text.split()[1])
        cur.execute("UPDATE users SET banned = 1 WHERE id = ?", (uid,))
        db.commit()
        bot.reply_to(msg, f"🚫 Banned {uid}")
    except Exception:
        bot.reply_to(msg, "Usage: /ban <user_id>")


@bot.message_handler(commands=["unban"])
def unban(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        uid = int(msg.text.split()[1])
        cur.execute("UPDATE users SET banned = 0 WHERE id = ?", (uid,))
        db.commit()
        bot.reply_to(msg, f"✅ Unbanned {uid}")
    except Exception:
        bot.reply_to(msg, "Usage: /unban <user_id>")


@bot.callback_query_handler(func=lambda call: True)
def handle(call):
    d = call.data

    if d == "verify":
        if is_joined(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Access granted!", show_alert=True)
            uid = call.from_user.id
            name = call.from_user.first_name or "friend"
            bot.send_photo(call.message.chat.id, BANNER,
                           caption=welcome_caption(name, uid),
                           parse_mode="HTML", reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ Join both channel and group first!", show_alert=True)
        return

    if d.startswith("a_"):
        if call.from_user.id != ADMIN_ID:
            return bot.answer_callback_query(call.id, "❌ Not allowed", show_alert=True)
        
        if d == "a_count":
            cur.execute("SELECT COUNT(*) FROM users")
            n = cur.fetchone()[0]
            bot.answer_callback_query(call.id, f"👥 {n} users", show_alert=True)
            
        elif d == "a_stats":
            bot.answer_callback_query(call.id)
            bot.send_message(call.from_user.id, "📊 Loading stats...")
            stats_cmd(call.message)
            
        elif d == "a_broadcast":
            broadcast_state.add(call.from_user.id)
            bot.send_message(call.from_user.id, "📢 Send the message to broadcast now.")
            bot.answer_callback_query(call.id)
        elif d == "a_ban":
            bot.answer_callback_query(call.id, "Send: /ban <user_id>", show_alert=True)
        elif d == "a_unban":
            bot.answer_callback_query(call.id, "Send: /unban <user_id>", show_alert=True)
        return

    if d == "profile":
        u = call.from_user
        bot.answer_callback_query(call.id, f"👤 {u.first_name}\n🆔 {u.id}", show_alert=True)
    elif d == "refresh":
        bot.answer_callback_query(call.id, "Refreshed ✅", show_alert=True)

@bot.message_handler(content_types=['photo'])
def get_id(msg):
    print("YOUR_NEW_ID:", msg.photo[-1].file_id)

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

print("Bot started...")
bot.infinity_polling()
