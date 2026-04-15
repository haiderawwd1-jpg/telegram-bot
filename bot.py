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
    status TEXT DEFAULT 'pending'
)
""")

cur.execute("INSERT OR IGNORE INTO leaders(user_id) VALUES(?)", (OWNER_ID,))
db.commit()

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

# ================= ID =================
@bot.message_handler(commands=["id"])
def myid(msg):
    bot.send_message(msg.chat.id, f"ID: {msg.chat.id}")

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
    bot.send_message(uid, "ارسل اسمك على فيس بوك")

@bot.message_handler(func=lambda m: m.text == "📊 عدد اللاعبين")
def count_users(m):
    n = cur.execute(
        "SELECT COUNT(*) FROM players WHERE status='accepted'"
    ).fetchone()[0]

    bot.send_message(m.chat.id, f"عدد اللاعبين: {n}")

@bot.message_handler(func=lambda m: m.text == "ℹ️ معلومات")
def info(m):
    bot.send_message(
        m.chat.id,
        "بوت تسجيل لاعبين الاتحاد العراقي"
    )

@bot.message_handler(func=lambda m: m.text == "📞 تواصل")
def contact(m):
    bot.send_message(
        m.chat.id,
        "للتواصل مع الإدارة: @username"
    )

# ================= ADMIN =================
@bot.message_handler(func=lambda m: m.text == "📥 الطلبات")
def requests_btn(m):
    if not is_leader(m.chat.id):
        return

    rows = cur.execute("""
        SELECT user_id,name,link,serial
        FROM players
        WHERE status='pending'
    """).fetchall()

    if not rows:
        bot.send_message(m.chat.id, "لا توجد طلبات")
        return

    for uid, name, link, serial in rows:
        kb = types.InlineKeyboardMarkup()
        kb.row(
            types.InlineKeyboardButton(
                "✅ قبول",
                callback_data=f"acc:{uid}"
            ),
            types.InlineKeyboardButton(
                "❌ رفض",
                callback_data=f"rej:{uid}"
            )
        )

        bot.send_message(
            m.chat.id,
            f"الاسم: {name}\nالرابط: {link}\nالتسلسلي: {serial}\nID: {uid}",
            reply_markup=kb
        )

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
    bot.send_message(
        m.chat.id,
        "ارسل نص الإعلان أو صورة مع تعليق"
    )

@bot.message_handler(func=lambda m: m.text == "➕ إضافة قائد")
def add_leader_btn(m):
    if not is_leader(m.chat.id):
        return

    steps[m.chat.id] = "addleader"
    bot.send_message(m.chat.id, "ارسل ID القائد")

@bot.message_handler(func=lambda m: m.text == "➖ حذف قائد")
def del_leader_btn(m):
    if not is_leader(m.chat.id):
        return

    steps[m.chat.id] = "delleader"
    bot.send_message(m.chat.id, "ارسل ID القائد للحذف")

# ================= CALLBACK =================
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

    elif action == "rej":
        cur.execute(
            "DELETE FROM players WHERE user_id=?",
            (uid,)
        )
        db.commit()
        bot.send_message(uid, "تم رفض طلبك ❌")

    bot.answer_callback_query(c.id, "تم")

# ================= ALL MESSAGES =================
@bot.message_handler(content_types=["text", "photo"])
def all_messages(m):
    uid = m.chat.id
    step = steps.get(uid)

    if not step:
        return

    if m.content_type == "text":
        txt = m.text.strip()

        # تسجيل
        if step == "name":
            cache[uid] = {"name": txt}
            steps[uid] = "link"
            bot.send_message(uid, "ارسل رابط صفحتك")
            return

        if step == "link":
            if "facebook.com" not in txt:
                bot.send_message(uid, "الرابط غير صحيح")
                return

            old = cur.execute(
                "SELECT 1 FROM players WHERE link=?",
                (txt,)
            ).fetchone()

            if old:
                bot.send_message(uid, "الرابط مستخدم")
                return

            cache[uid]["link"] = txt
            steps[uid] = "serial"
            bot.send_message(uid, "ارسل الرقم التسلسلي")
            return

        if step == "serial":
            old = cur.execute(
                "SELECT 1 FROM players WHERE serial=?",
                (txt,)
            ).fetchone()

            if old:
                bot.send_message(uid, "الرقم مستخدم")
                return

            cur.execute("""
                INSERT INTO players(
                    user_id,name,link,serial,status
                ) VALUES(?,?,?,?,?)
            """, (
                uid,
                cache[uid]["name"],
                cache[uid]["link"],
                txt,
                "pending"
            ))
            db.commit()

            steps.pop(uid, None)
            cache.pop(uid, None)

            bot.send_message(uid, "تم إرسال طلبك للمراجعة")
            return

        # بحث
        if step == "search":
            rows = cur.execute("""
                SELECT user_id,name,link,serial,status
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
                bot.send_message(
                    uid,
                    f"ID: {r[0]}\nالاسم: {r[1]}\nالرابط: {r[2]}\nالتسلسلي: {r[3]}\nالحالة: {r[4]}"
                )
            return

        # إعلان نص
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
            bot.send_message(uid, f"تم الإرسال إلى {sent} لاعب")
            return

        # إضافة قائد
        if step == "addleader" and txt.isdigit():
            cur.execute(
                "INSERT OR IGNORE INTO leaders VALUES(?)",
                (int(txt),)
            )
            db.commit()
            steps.pop(uid, None)
            bot.send_message(uid, "تمت الإضافة")
            return

        # حذف قائد
        if step == "delleader" and txt.isdigit():
            cur.execute(
                "DELETE FROM leaders WHERE user_id=? AND user_id!=?",
                (int(txt), OWNER_ID)
            )
            db.commit()
            steps.pop(uid, None)
            bot.send_message(uid, "تم الحذف")
            return

    # إعلان صورة
    if m.content_type == "photo" and step == "broadcast":
        users = cur.execute("""
            SELECT user_id FROM players
            WHERE status='accepted'
        """).fetchall()

        sent = 0
        caption = m.caption if m.caption else ""

        for u in users:
            try:
                bot.send_photo(
                    u[0],
                    m.photo[-1].file_id,
                    caption=caption
                )
                sent += 1
            except:
                pass

        steps.pop(uid, None)
        bot.send_message(uid, f"تم إرسال الصورة إلى {sent} لاعب")

# ================= RUN =================
while True:
    try:
        bot.infinity_polling(skip_pending=True)
    except:
        time.sleep(5)
