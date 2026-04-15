import telebot
from telebot import types
import sqlite3
import re

TOKEN = "8629150475:AAFQcvsiNvndJIh3JuPK6pkEIFnxl3XFkq4"
OWNER_ID = 653170487
CHANNEL_USERNAME = "@mu_un1"

bot = telebot.TeleBot(TOKEN)

db = sqlite3.connect("players.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS players(
user_id INTEGER PRIMARY KEY,
name TEXT,
link TEXT,
serial TEXT
)
""")
db.commit()

users = {}

def subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📝 تسجيل", "📋 عدد اللاعبين")
    kb.row("📞 تواصل", "ℹ️ معلومات")
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    users.pop(message.chat.id, None)

    if not subscribed(message.chat.id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            "اشترك بالقناة",
            url="https://t.me/mu_un1"
        ))
        bot.send_message(
            message.chat.id,
            "يجب الاشتراك بالقناة للتسجيل",
            reply_markup=kb
        )
        return

    bot.send_message(
        message.chat.id,
        "اهلا بك في الاتحاد العراقي للكلانات",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['id'])
def get_id(message):
    bot.send_message(message.chat.id, f"ايديك: {message.chat.id}")

@bot.message_handler(func=lambda m: True)
def all_messages(message):
    uid = message.chat.id
    text = message.text

    if text == "📝 تسجيل":
        users[uid] = {"step": "name"}
        bot.send_message(uid, "ارسل اسمك على فيس بوك")
        return

    if text == "📋 عدد اللاعبين":
        count = cur.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        bot.send_message(uid, f"عدد اللاعبين المسجلين: {count}")
        return

    if text == "📞 تواصل":
        bot.send_message(uid, "للتواصل مع الادارة: @username")
        return

    if text == "ℹ️ معلومات":
        bot.send_message(uid, "بوت تسجيل لاعبين الاتحاد العراقي للكلانات")
        return

    if uid in users:
        step = users[uid]["step"]

        if step == "name":
            users[uid]["name"] = text
            users[uid]["step"] = "link"
            bot.send_message(uid, "ارسل رابط صفحتك على فيس بوك")
            return

        elif step == "link":
            if "facebook.com" not in text:
                bot.send_message(uid, "الرابط غير صحيح")
                return

            users[uid]["link"] = text
            users[uid]["step"] = "serial"
            bot.send_message(uid, "ارسل التسلسلي")
            return

        elif step == "serial":
            users[uid]["serial"] = text

            cur.execute(
                "INSERT OR REPLACE INTO players VALUES (?, ?, ?, ?)",
                (
                    uid,
                    users[uid]["name"],
                    users[uid]["link"],
                    users[uid]["serial"]
                )
            )
            db.commit()

            bot.send_message(
                uid,
                "تم التسجيل بنجاح ✅",
                reply_markup=main_menu()
            )

            users.pop(uid, None)

bot.infinity_polling()
