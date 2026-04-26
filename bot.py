import telebot
from telebot import types
import sqlite3
import time
import json

TOKEN = "8629150475:AAFQcvsiNvndJIh3JuPK6pkEIFnxl3XFkq4"
OWNER_ID = 653170487
CHANNEL = "@mu_un1"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

db = sqlite3.connect("players.db", check_same_thread=False)
cur = db.cursor()

# ================= BACKUP =================
def backup_players():
    rows = cur.execute("SELECT * FROM players").fetchall()
    with open("backup.json", "w", encoding="utf-8") as f:
        json.dump(rows, f)

def restore_backup():
    try:
        with open("backup.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for row in data:
                try:
                    cur.execute("""
                    INSERT OR IGNORE INTO players
                    (user_id,name,link,serial,status,screen_file_id)
                    VALUES(?,?,?,?,?,?)
                    """, row)
                except:
                    pass
            db.commit()
    except:
        pass

# ================= DATABASE =================
cur.execute("""
CREATE TABLE IF NOT EXISTS leaders(
    user_id INTEGER PRIMARY KEY
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS players(
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    link TEXT UNIQUE,
    serial TEXT UNIQUE,
    status TEXT DEFAULT 'pending',
    screen_file_id TEXT
)
""")

cur.execute("INSERT OR IGNORE INTO leaders(user_id) VALUES(?)", (OWNER_ID,))
db.commit()

# 🔥 استرجاع النسخة الاحتياطية
restore_backup()

steps = {}
cache = {}

# ================= HELPERS =================
def is_leader(uid):
    return cur.execute(
        "SELECT 1 FROM leaders WHERE user_id=?",
        (uid,)
    ).fetchone() is not None

def subscribed(uid):
    if is_leader(uid):
        return True
    try:
        member = bot.get_chat_member(CHANNEL, uid)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def user_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📝 تسجيل", "📊 عدد اللاعبين")
    kb.row("ℹ️ معلومات", "📞 تواصل")
    return kb

def admin_menu():
    kb = user_menu()
    kb.row("📥 الطلبات", "🔍 بحث لاعب")
    kb.row("📢 إعلان")
    kb.row("➕ إضافة قائد", "➖ حذف قائد")
    return kb

def send_home(uid):
    if is_leader(uid):
        bot.send_message(uid, "👑 لوحة القائد", reply_markup=admin_menu())
    else:
        bot.send_message(uid, "أهلاً بك", reply_markup=user_menu())

# ================= START =================
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.chat.id
    steps.pop(uid, None)
    cache.pop(uid, None)

    if not subscribed(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            "اشترك بالقناة",
            url="https://t.me/mu_un1"
        ))
        bot.send_message(
            uid,
            "يجب الاشتراك بالقناة ثم أرسل /start",
            reply_markup=kb
        )
        return

    send_home(uid)

# ================= BUTTONS =================
@bot.message_handler(func=lambda m: m.text == "📝 تسجيل")
def register(m):
    uid = m.chat.id

    if not subscribed(uid):
        start(m)
        return

    if cur.execute(
        "SELECT 1 FROM players WHERE user_id=?",
        (uid,)
    ).fetchone():
        bot.send_message(uid, "أنت مسجل مسبقاً")
        return

    steps[uid] = "name"
    bot.send_message(uid, "ارسل اسمك")

@bot.message_handler(func=lambda m: m.text == "📊 عدد اللاعبين")
def count_users(m):
    n = cur.execute(
        "SELECT COUNT(*) FROM players WHERE status='accepted'"
    ).fetchone()[0]

    bot.send_message(m.chat.id, f"عدد اللاعبين: {n}")

# ================= ALL =================
@bot.message_handler(content_types=["text", "photo"])
def all_messages(m):
    uid = m.chat.id
    step = steps.get(uid)

    if not step:
        return

    if m.content_type == "text":
        txt = m.text.strip()

        if step == "name":
            cache[uid] = {"name": txt}
            steps[uid] = "link"
            bot.send_message(uid, "ارسل رابط الفيس")
            return

        if step == "link":
            cache[uid]["link"] = txt
            steps[uid] = "serial"
            bot.send_message(uid, "ارسل الرقم التسلسلي")
            return

        if step == "serial":
            cache[uid]["serial"] = txt
            steps[uid] = "screen"
            bot.send_message(uid, "ارسل سكرين الرقم التسلسلي")
            return

    if m.content_type == "photo":
        if step == "screen":
            file_id = m.photo[-1].file_id

            cur.execute("""
                INSERT INTO players(
                    user_id,name,link,serial,status,screen_file_id
                ) VALUES(?,?,?,?,?,?)
            """, (
                uid,
                cache[uid]["name"],
                cache[uid]["link"],
                cache[uid]["serial"],
                "pending",
                file_id
            ))
            db.commit()

            # 🔥 backup
            backup_players()

            steps.pop(uid, None)
            cache.pop(uid, None)

            bot.send_message(uid, "تم إرسال طلبك للمراجعة ✅")

# ================= RUN =================
while True:
    try:
        bot.infinity_polling(skip_pending=True)
    except:
        time.sleep(5)
