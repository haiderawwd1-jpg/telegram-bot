import telebot
from telebot import types
import sqlite3
import time

TOKEN = "PUT_TOKEN_HERE"
OWNER_ID = 653170487
CHANNEL = "@mu_un1"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

db = sqlite3.connect("players.db", check_same_thread=False)
cur = db.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS leaders (user_id INTEGER PRIMARY KEY)")
cur.execute("INSERT OR IGNORE INTO leaders(user_id) VALUES (?)", (OWNER_ID,))
db.commit()

steps = {}

# ================= HELPERS =================
def is_leader(uid):
    x = cur.execute("SELECT user_id FROM leaders WHERE user_id=?", (uid,)).fetchone()
    return x is not None

def subscribed(uid):
    if is_leader(uid):
        return True
    try:
        m = bot.get_chat_member(CHANNEL, uid)
        return m.status in ["member", "administrator", "creator"]
    except:
        return False

def user_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📝 تسجيل", "📊 عدد اللاعبين")
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📝 تسجيل", "📊 عدد اللاعبين")
    kb.row("📥 الطلبات", "🔍 بحث لاعب")
    kb.row("📢 إعلان", "➕ إضافة قائد")
    kb.row("➖ حذف قائد")
    return kb

def send_home(uid):
    if is_leader(uid):
        bot.send_message(uid, "لوحة القائد", reply_markup=admin_menu())
    else:
        bot.send_message(uid, "اهلا وسهلا بك في الاتحاد العراقي", reply_markup=user_menu())

# ================= START =================
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.chat.id
    steps.pop(uid, None)   # يرجع للبداية من أي خطوة

    if not subscribed(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("اشترك بالقناة", url="https://t.me/mu_un1"))
        bot.send_message(uid, "يجب الاشتراك بالقناة أولاً ثم اضغط /start", reply_markup=kb)
        return

    send_home(uid)

# ================= ID =================
@bot.message_handler(commands=['id'])
def myid(msg):
    bot.send_message(msg.chat.id, f"ID: {msg.chat.id}")

# ================= BUTTONS =================
@bot.message_handler(func=lambda m: m.text == "📊 عدد اللاعبين")
def count_users(m):
    bot.send_message(m.chat.id, "العداد يشتغل بعد إضافة قاعدة اللاعبين")

@bot.message_handler(func=lambda m: m.text == "📥 الطلبات")
def requests_btn(m):
    if is_leader(m.chat.id):
        bot.send_message(m.chat.id, "طلبات التسجيل ستظهر هنا")

@bot.message_handler(func=lambda m: m.text == "🔍 بحث لاعب")
def search_btn(m):
    if is_leader(m.chat.id):
        bot.send_message(m.chat.id, "ارسل اسم اللاعب أو رابطه")

@bot.message_handler(func=lambda m: m.text == "📢 إعلان")
def ads_btn(m):
    if is_leader(m.chat.id):
        bot.send_message(m.chat.id, "ارسل نص الإعلان")

@bot.message_handler(func=lambda m: m.text == "➕ إضافة قائد")
def add_leader(m):
    if is_leader(m.chat.id):
        bot.send_message(m.chat.id, "ارسل ID القائد الجديد")

@bot.message_handler(func=lambda m: m.text == "➖ حذف قائد")
def del_leader(m):
    if is_leader(m.chat.id):
        bot.send_message(m.chat.id, "ارسل ID القائد للحذف")

# ================= RUN =================
while True:
    try:
        bot.infinity_polling(skip_pending=True)
    except:
        time.sleep(5)
