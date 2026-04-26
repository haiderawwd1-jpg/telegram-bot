import telebot
from telebot import types
import sqlite3
import time

TOKEN = "8629150475:AAFQcvsiNvndJIh3JuPK6pkEIFnxl3XFkq4"
OWNER_ID = 653170487
CHANNEL = "@mu_un1"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

db = sqlite3.connect("players.db", check_same_thread=False)
cur = db.cursor()

================= DATABASE =================

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

try:
cur.execute("ALTER TABLE players ADD COLUMN screen_file_id TEXT")
except:
pass

cur.execute("INSERT OR IGNORE INTO leaders(user_id) VALUES(?)", (OWNER_ID,))
db.commit()

steps = {}
cache = {}

================= HELPERS =================

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

================= START =================

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

================= BUTTONS =================

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

@bot.message_handler(func=lambda m: m.text == "ℹ️ معلومات")
def info(m):
bot.send_message(m.chat.id, "بوت تسجيل اللاعبين")

@bot.message_handler(func=lambda m: m.text == "📞 تواصل")
def contact(m):
bot.send_message(m.chat.id, "@username")

================= ADMIN =================

@bot.message_handler(func=lambda m: m.text == "📥 الطلبات")
def requests_btn(m):
if not is_leader(m.chat.id):
return

rows = cur.execute("""  
    SELECT user_id,name,link,serial,screen_file_id  
    FROM players  
    WHERE status='pending'  
""").fetchall()  

if not rows:  
    bot.send_message(m.chat.id, "لا توجد طلبات")  
    return  

for uid, name, link, serial, screen in rows:  
    kb = types.InlineKeyboardMarkup()  
    kb.row(  
        types.InlineKeyboardButton("✅ قبول", callback_data=f"acc:{uid}"),  
        types.InlineKeyboardButton("❌ رفض", callback_data=f"rej:{uid}")  
    )  

    txt = f"""الاسم: {name}

الرابط: {link}
التسلسلي: {serial}
ID: {uid}"""

if screen:  
        bot.send_photo(m.chat.id, screen, caption=txt, reply_markup=kb)  
    else:  
        bot.send_message(m.chat.id, txt, reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "🔍 بحث لاعب")
def search_btn(m):
if not is_leader(m.chat.id):
return

steps[m.chat.id] = "search"  
bot.send_message(m.chat.id, "ارسل اسم اللاعب أو رابطه")

@bot.message_handler(func=lambda m: m.text == "📢 إعلان")
def ad_btn(m):
if not is_leader(m.chat.id):
return

steps[m.chat.id] = "broadcast"  
bot.send_message(m.chat.id, "ارسل نص أو صورة مع تعليق")

@bot.message_handler(func=lambda m: m.text == "➕ إضافة قائد")
def add_leader(m):
if not is_leader(m.chat.id):
return

steps[m.chat.id] = "addleader"  
bot.send_message(m.chat.id, "ارسل ID")

@bot.message_handler(func=lambda m: m.text == "➖ حذف قائد")
def del_leader(m):
if not is_leader(m.chat.id):
return

steps[m.chat.id] = "delleader"  
bot.send_message(m.chat.id, "ارسل ID")

================= CALLBACK =================

@bot.callback_query_handler(func=lambda c: True)
def callback(c):
if not is_leader(c.message.chat.id):
return

action, uid = c.data.split(":")  
uid = int(uid)  

if action == "acc":  
    cur.execute(  
        "UPDATE players SET status='accepted' WHERE user_id=?",  
        (uid,)  
    )  
    db.commit()  

    bot.send_message(uid, "تم قبول طلبك ✅")  

    try:  
        bot.edit_message_caption(  
            caption=c.message.caption + "\n\n✅ تم قبول الطلب",  
            chat_id=c.message.chat.id,  
            message_id=c.message.message_id,  
            reply_markup=None  
        )  
    except:  
        bot.edit_message_text(  
            c.message.text + "\n\n✅ تم قبول الطلب",  
            c.message.chat.id,  
            c.message.message_id,  
            reply_markup=None  
        )  

elif action == "rej":  
    cur.execute(  
        "DELETE FROM players WHERE user_id=?",  
        (uid,)  
    )  
    db.commit()  

    bot.send_message(uid, "تم رفض طلبك ❌")  

    try:  
        bot.edit_message_caption(  
            caption=c.message.caption + "\n\n❌ تم رفض الطلب",  
            chat_id=c.message.chat.id,  
            message_id=c.message.message_id,  
            reply_markup=None  
        )  
    except:  
        bot.edit_message_text(  
            c.message.text + "\n\n❌ تم رفض الطلب",  
            c.message.chat.id,  
            c.message.message_id,  
            reply_markup=None  
        )  

bot.answer_callback_query(c.id, "تم")

================= ALL =================

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

    if step == "search":  
        rows = cur.execute("""  
            SELECT user_id,name,link,serial,status,screen_file_id  
            FROM players  
            WHERE name LIKE ? OR link LIKE ?  
        """, (  
            f"%{txt}%",  
            f"%{txt}%"  
        )).fetchall()  

        steps.pop(uid, None)  

        if not rows:  
            bot.send_message(uid, "لا توجد نتائج")  
            return  

        for r in rows:  
            msg = f"""ID: {r[0]}

الاسم: {r[1]}
الرابط: {r[2]}
التسلسلي: {r[3]}
الحالة: {r[4]}"""

if r[5]:  
                bot.send_photo(uid, r[5], caption=msg)  
            else:  
                bot.send_message(uid, msg)  
        return  

    if step == "broadcast":  
        users = cur.execute("""  
            SELECT user_id FROM players  
            WHERE status='accepted'  
        """).fetchall()  

        sent = 0  
        for u in users:  
            try:  
                bot.send_message(u[0], txt)  
                sent += 1  
            except:  
                pass  

        steps.pop(uid, None)  
        bot.send_message(uid, f"تم الإرسال إلى {sent}")  
        return  

    if step == "addleader" and txt.isdigit():  
        cur.execute(  
            "INSERT OR IGNORE INTO leaders VALUES(?)",  
            (int(txt),)  
        )  
        db.commit()  
        steps.pop(uid, None)  
        bot.send_message(uid, "تمت الإضافة")  
        return  

    if step == "delleader" and txt.isdigit():  
        cur.execute(  
            "DELETE FROM leaders WHERE user_id=? AND user_id!=?",  
            (int(txt), OWNER_ID)  
        )  
        db.commit()  
        steps.pop(uid, None)  
        bot.send_message(uid, "تم الحذف")  
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

        steps.pop(uid, None)  
        cache.pop(uid, None)  

        bot.send_message(uid, "تم إرسال طلبك للمراجعة ✅")  
        return  

    if step == "broadcast":  
        users = cur.execute("""  
            SELECT user_id FROM players  
            WHERE status='accepted'  
        """).fetchall()  

        sent = 0  
        cap = m.caption if m.caption else ""  

        for u in users:  
            try:  
                bot.send_photo(  
                    u[0],  
                    m.photo[-1].file_id,  
                    caption=cap  
                )  
                sent += 1  
            except:  
                pass  

        steps.pop(uid, None)  
        bot.send_message(uid, f"تم إرسال الصورة إلى {sent}")

================= RUN =================

while True:
try:
bot.infinity_polling(skip_pending=True)
except:
time.sleep(5)
