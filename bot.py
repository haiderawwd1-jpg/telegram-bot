import telebot
from telebot import types
import sqlite3
import time
import re
import datetime

TOKEN = "8629150475:AAFQcvsiNvndJIh3JuPK6pkEIFnxl3XFkq4"
OWNER_ID = 653170487
CHANNEL_USERNAME = "@mu_un1"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

db = sqlite3.connect("players.db", check_same_thread=False)
cur = db.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS players (user_id INTEGER PRIMARY KEY, name TEXT, fb_link TEXT UNIQUE, serial TEXT UNIQUE, photo TEXT, status TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS leaders (user_id INTEGER PRIMARY KEY)")
cur.execute("INSERT OR IGNORE INTO leaders VALUES (?)", (OWNER_ID,))
db.commit()

temp = {}

def is_leader(uid):
    x = cur.execute("SELECT user_id FROM leaders WHERE user_id=?", (uid,)).fetchone()
    return x is not None

def subscribed(user_id):
    try:
        st = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return st in ["member", "administrator", "creator"]
    except:
        return False

def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📝 تسجيل", "📋 عدد اللاعبين")
    kb.row("🔎 بحث", "📢 اعلان")
    kb.row("➕ اضافة قائد", "➖ حذف قائد")
    return kb

@bot.message_handler(commands=['start'])
def start(msg):
    if not subscribed(msg.chat.id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("اشترك بالقناة", url="https://t.me/mu_un1"))
        bot.send_message(msg.chat.id, "يجب الاشتراك بالقناة للتسجيل", reply_markup=kb)
        return
    bot.send_message(msg.chat.id, "اهلا وسهلا بك في الاتحاد العراقي", reply_markup=menu())

@bot.message_handler(func=lambda m: m.text == "📝 تسجيل")
def reg(msg):
    x = cur.execute("SELECT * FROM players WHERE user_id=?", (msg.chat.id,)).fetchone()
    if x:
        bot.send_message(msg.chat.id, "مسجل مسبقاً")
        return
    temp[msg.chat.id] = {}
    a = bot.send_message(msg.chat.id, "ارسل اسمك على فيس بوك")
    bot.register_next_step_handler(a, get_name)

def get_name(msg):
    temp[msg.chat.id]["name"] = msg.text
    a = bot.send_message(msg.chat.id, "ارسل رابط صفحتك على فيس بوك")
    bot.register_next_step_handler(a, get_link)

def get_link(msg):
    if "facebook.com" not in msg.text and "fb.com" not in msg.text:
        a = bot.send_message(msg.chat.id, "الرابط غير صحيح")
        bot.register_next_step_handler(a, get_link)
        return
    old = cur.execute("SELECT * FROM players WHERE fb_link=?", (msg.text,)).fetchone()
    if old:
        bot.send_message(msg.chat.id, "الرابط مستخدم مسبقاً")
        return
    temp[msg.chat.id]["link"] = msg.text
    a = bot.send_message(msg.chat.id, "ارسل الرقم التسلسلي")
    bot.register_next_step_handler(a, get_serial)

def get_serial(msg):
    old = cur.execute("SELECT * FROM players WHERE serial=?", (msg.text,)).fetchone()
    if old:
        bot.send_message(msg.chat.id, "الرقم مستخدم مسبقاً")
        return
    temp[msg.chat.id]["serial"] = msg.text
    a = bot.send_message(msg.chat.id, "ارسل سكرين الرقم التسلسلي")
    bot.register_next_step_handler(a, get_photo)

def get_photo(msg):
    if not msg.photo:
        a = bot.send_message(msg.chat.id, "ارسل صورة فقط")
        bot.register_next_step_handler(a, get_photo)
        return
    data = temp[msg.chat.id]
    cur.execute("INSERT INTO players VALUES (?,?,?,?,?,?)",
                (msg.chat.id, data["name"], data["link"], data["serial"], msg.photo[-1].file_id, "pending"))
    db.commit()

    txt = f"""طلب جديد

الاسم: {data["name"]}
الرابط: {data["link"]}
التسلسلي: {data["serial"]}
الايدي: {msg.chat.id}"""

    leaders = cur.execute("SELECT user_id FROM leaders").fetchall()
    for l in leaders:
        kb = types.InlineKeyboardMarkup()
        kb.row(
            types.InlineKeyboardButton("✅ قبول", callback_data=f"ok_{msg.chat.id}"),
            types.InlineKeyboardButton("❌ رفض", callback_data=f"no_{msg.chat.id}")
        )
        bot.send_photo(l[0], msg.photo[-1].file_id, caption=txt, reply_markup=kb)

    bot.send_message(msg.chat.id, "جاري التحقق من طلبك")

@bot.callback_query_handler(func=lambda c: True)
def call(c):
    if not is_leader(c.from_user.id):
        return
    uid = int(c.data.split("_")[1])
    if c.data.startswith("ok_"):
        cur.execute("UPDATE players SET status='accepted' WHERE user_id=?", (uid,))
        db.commit()
        bot.send_message(uid, "تم قبول طلبك ✅")
    if c.data.startswith("no_"):
        cur.execute("DELETE FROM players WHERE user_id=?", (uid,))
        db.commit()
        bot.send_message(uid, "طلبك مرفوض ❌ تأكد من معلوماتك وحاول مجدداً")

@bot.message_handler(func=lambda m: m.text == "📋 عدد اللاعبين")
def count(m):
    n = cur.execute("SELECT COUNT(*) FROM players WHERE status='accepted'").fetchone()[0]
    bot.send_message(m.chat.id, f"عدد اللاعبين المسجلين: {n}")

while True:
    try:
        bot.infinity_polling()
    except:
        time.sleep(5)
