import telebot from telebot import  import sqlite3 import time

TOKEN = "PUT_TOKEN_HERE" OWNER_ID = 653170487 CHANNEL = "@mu_un1"

bot = telebot.TeleBot(TOKEN) steps = {} temp = {} users = {}

db = sqlite3.connect('players.db', check_same_thread=False) cur = db.cursor() cur.execute('CREATE TABLE IF NOT EXISTS leaders (user_id INTEGER PRIMARY KEY)') cur.execute('INSERT OR IGNORE INTO leaders(user_id) VALUES (?)', (OWNER_ID,)) db.commit()

def is_leader(uid): return cur.execute('SELECT 1 FROM leaders WHERE user_id=?', (uid,)).fetchone() is not None

def subscribed(uid): if is_leader(uid): return True try: m = bot.get_chat_member(CHANNEL, uid) return m.status in ['member','administrator','creator'] except: return False

def menu(uid): kb = types.ReplyKeyboardMarkup(resize_keyboard=True) kb.row('📝 تسجيل', '📊 عدد اللاعبين') if is_leader(uid): kb.row('👑 القادة') return kb

def send_home(uid): bot.send_message(uid, 'اهلا وسهلا بك', reply_markup=menu(uid))

@bot.message_handler(commands=['start']) def start(msg): uid = msg.chat.id steps.pop(uid, None) temp.pop(uid, None) users.pop(uid, None) if not subscribed(uid): kb = types.InlineKeyboardMarkup() kb.add(types.InlineKeyboardButton('اشترك بالقناة', url='https://t.me/mu_un1')) bot.send_message(uid, 'يجب الاشتراك بالقناة للتسجيل', reply_markup=kb) return send_home(uid)

@bot.message_handler(func=lambda m: m.text == '📝 تسجيل') def reg(m): steps[m.chat.id] = 'name' bot.send_message(m.chat.id, 'ارسل اسمك على فيس بوك')

@bot.message_handler(func=lambda m: m.text == '📊 عدد اللاعبين') def count_btn(m): bot.send_message(m.chat.id, 'عدد اللاعبين سيضاف لاحقاً')

@bot.message_handler(func=lambda m: m.text == '👑 القادة') def leaders_btn(m): if is_leader(m.chat.id): bot.send_message(m.chat.id, 'انت قائد ومخول')

@bot.message_handler(func=lambda m: True) def all_msgs(m): uid = m.chat.id if m.text == '/start': start(m) return if uid not in steps: return if steps[uid] == 'name': temp[uid] = {'name': m.text} steps[uid] = 'link' bot.send_message(uid, 'ارسل رابط صفحتك على فيس بوك') return if steps[uid] == 'link': if 'facebook.com' not in m.text: bot.send_message(uid, 'الرابط غير صحيح') return temp[uid]['link'] = m.text steps[uid] = 'serial' bot.send_message(uid, 'ارسل الرقم التسلسلي') return if steps[uid] == 'serial': temp[uid]['serial'] = m.text bot.send_message(uid, 'تم استلام طلبك ✅') steps.pop(uid, None) temp.pop(uid, None)

while True: try: bot.infinity_polling(skip_pending=True) except: time.sleep(5)
