import telebot
from telebot import types
import time

TOKEN = "8629150475:AAFQcvsiNvndJIh3JuPK6pkEIFnxl3XFkq4"
ADMIN_ID = 653170487

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

users = {}

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📝 تسجيل", "📋 عدد اللاعبين")
    kb.row("📞 تواصل", "ℹ️ معلومات")
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    text = """
اهلا وسهلا بك في الاتحاد العراقي

يجب ان ترسل:
اسمك على فيس بوك
رابط صفحتك على فيس بوك
الرقم التسلسلي للجهاز
صورة سكرين للرقم التسلسلي

سيتم التدقيق من قبل الادمنية
"""
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📋 عدد اللاعبين")
def players(message):
    bot.send_message(message.chat.id, f"عدد المسجلين: {len(users)}")

@bot.message_handler(func=lambda m: m.text == "📞 تواصل")
def contact(message):
    bot.send_message(message.chat.id, "راسل الادمن:\n@username")

@bot.message_handler(func=lambda m: m.text == "ℹ️ معلومات")
def info(message):
    bot.send_message(message.chat.id, "بوت تسجيل اللاعبين الرسمي")

@bot.message_handler(func=lambda m: m.text == "📝 تسجيل")
def register(message):
    msg = bot.send_message(message.chat.id, "ارسل اسمك على فيس بوك:")
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    users[message.chat.id] = {"name": message.text}
    msg = bot.send_message(message.chat.id, "ارسل رابط صفحتك على فيس بوك:")
    bot.register_next_step_handler(msg, get_link)

def get_link(message):
    users[message.chat.id]["link"] = message.text
    msg = bot.send_message(message.chat.id, "ارسل الرقم التسلسلي:")
    bot.register_next_step_handler(msg, get_serial)

def get_serial(message):
    users[message.chat.id]["serial"] = message.text
    msg = bot.send_message(message.chat.id, "ارسل صورة سكرين للرقم التسلسلي:")
    bot.register_next_step_handler(msg, get_photo)

def get_photo(message):
    if not message.photo:
        msg = bot.send_message(message.chat.id, "ارسل صورة فقط:")
        bot.register_next_step_handler(msg, get_photo)
        return

    data = users[message.chat.id]
    caption = f"""
طلب تسجيل جديد:

الاسم: {data['name']}
الرابط: {data['link']}
التسلسلي: {data['serial']}
الايدي: {message.chat.id}
"""

    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption)
    bot.send_message(message.chat.id, "تم ارسال طلبك بنجاح ✅", reply_markup=main_menu())

while True:
    try:
        print("BOT RUNNING...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
    except Exception as e:
        print("RECONNECTING...", e)
        time.sleep(5)
