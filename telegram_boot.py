import telebot
import requests
import time
import json
import os
import threading
import urllib.request
from datetime import datetime, timezone
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

# ===== CONFIG =====
BOT_TOKEN = "8791038778:AAH6hI45NA-ADCzv82qFPG2QVT2CCRT9its"
bot = telebot.TeleBot(BOT_TOKEN)

ALLOWED_GROUP_ID = -1003564455189
API_INFO_URL = "https://info-ob49.onrender.com/api/account/"
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

REQUIRED_CHATS = [
    {"id": "@zadxproooo", "name": "Канал 1", "url": "https://t.me/zadxproooo"},
    {"id": "@zadxprootziv", "name": "Канал 2", "url": "https://t.me/zadxprootziv"},
    {"id": "@groupzadxpro", "name": "Гуруҳи мо", "url": "https://t.me/groupzadxpro"}
]

ALL_REGIONS = ["ru", "sg", "ind", "br", "me", "us", "id", "pk", "bd", "cis", "tw", "vn", "th"]

# ===== KEEP ALIVE =====
def keep_alive():
    while True:
        try:
            urllib.request.urlopen(RENDER_URL)
            print("✅ Keep alive!")
        except:
            pass
        time.sleep(300)

# ===== ФУНКСИЯҲО =====
def escape_md(text):
    if not text:
        return "Холӣ"
    text = str(text)
    for ch in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(ch, f'\\{ch}')
    return text

def format_date(unix_timestamp):
    try:
        if not unix_timestamp or int(unix_timestamp) == 0:
            return "Маълумот нест"
        return datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc).strftime('%d.%m.%Y %H:%M')
    except:
        return "Маълумот нест"

def get_not_subscribed(user_id):
    not_joined = []
    for chat in REQUIRED_CHATS:
        try:
            member = bot.get_chat_member(chat['id'], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append(chat)
        except:
            not_joined.append(chat)
    return not_joined

def get_ff_player(player_id):
    for reg in ALL_REGIONS:
        try:
            r = requests.get(API_INFO_URL, params={"uid": player_id, "region": reg}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("basicInfo", {}).get("nickname"):
                    return data, reg.upper()
        except:
            continue
    return None, None

# ===== HANDLERS =====
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    if message.chat.id != ALLOWED_GROUP_ID:
        return
    for new_user in message.new_chat_members:
        if new_user.id == bot.get_me().id:
            continue
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="📜 КОМАНДАҲО", callback_data="show_help"))
        bot.send_message(
            message.chat.id,
            f"Ассалому алейкум, {new_user.first_name}! 👋\n"
            f"Хуш омадед ба гурӯҳи мо.\n"
            f"Барои дидани командаҳо тугмаро пахш кунед.",
            reply_markup=markup
        )

@bot.message_handler(commands=['help'])
def help_handler(message):
    help_text = (
        "📜 ДАСТУРАМАЛИ КОМАНДАҲО:\n\n"
        "👉 /check ID - Тафтиши пурраи аккаунт\n"
        "👉 /start - Оғози бот\n\n"
        "📢 Бот танҳо барои аъзоёни каналҳои мо кор мекунад!"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['start'])
def start_handler(message):
    not_sub = get_not_subscribed(message.from_user.id)
    if not_sub:
        markup = InlineKeyboardMarkup()
        for chat in not_sub:
            markup.add(InlineKeyboardButton(text=f"📢 {chat['name']}", url=chat['url']))
        bot.send_message(
            message.chat.id,
            "❗ Аввал ба каналҳо обуна шав:",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            "✅ Хуш омадед!\n\nДар гурӯҳ /check ID нависед."
        )

@bot.message_handler(commands=['check'])
def check_id_command(message):
    if message.chat.id != ALLOWED_GROUP_ID:
        return

    if get_not_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ Аввал ба каналҳо обуна шавед!")
        return

    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message, "❓ Намуна: /check 8898233939")
        return

    player_id = args[-1]
    wait_msg = bot.reply_to(message, f"📡 Ҷустуҷӯ: {player_id}...")

    data, region = get_ff_player(player_id)
    if not data:
        bot.edit_message_text("❌ ID ёфт нашуд!", message.chat.id, wait_msg.message_id)
        return

    b = data.get("basicInfo", {})
    s = data.get("socialInfo", {})
    c = data.get("clanBasicInfo", {})
    cr = data.get("creditScoreInfo", {})

    nickname = str(b.get('nickname', '?'))
    bio = str(s.get('signature', 'Холӣ'))
    clan_name = str(c.get('clanName', 'Нест'))

    last_log = int(b.get("lastLoginAt", 0))
    days_off = int((time.time() - last_log) / 86400) if last_log > 0 else 0
    status = "🟢 ФАЪОЛ" if days_off < 7 else "🔴 ОФЛАЙН"

    text = (
        f"📂 МАЪЛУМОТИ ПУРРАИ АККАУНТ\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Никнейм: {nickname}\n"
        f"🆔 ID: {player_id}\n"
        f"🌍 Регион: {region}\n"
        f"🛡 Статус: {status}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Сатҳ: {b.get('level','?')}\n"
        f"📈 Таҷриба: {b.get('exp','?')}\n"
        f"❤️ Лайкҳо: {b.get('liked',0)}\n"
        f"🏆 Ранг: {b.get('rank', '?')}\n"
        f"📉 Кредит: {cr.get('creditScore', 100)}/100\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏰 Клан: {clan_name}\n"
        f"🆔 ID Клан: {c.get('clanId','0')}\n"
        f"🎖 Сатҳи Клан: {c.get('clanLevel','?')}\n"
        f"👥 Аъзоён: {c.get('memberNum','?')}/{c.get('capacity','?')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 Охирин бор: {format_date(last_log)}\n"
        f"📅 Сохта шуд: {format_date(b.get('createAt', 0))}\n"
        f"⏳ Офлайн: {days_off} руз\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 Bio: {bio}\n"
        f"🌐 Забон: {s.get('language','?')}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    try:
        bot.edit_message_text(text, message.chat.id, wait_msg.message_id)
    except Exception as e:
        print(f"Хато: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "show_help")
def callback_help(call):
    bot.answer_callback_query(call.id)
    help_handler(call.message)

# ===== ОҒОЗ =====
print("🚀 Бот фаъол шуд!")

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))), daemon=True).start()
threading.Thread(target=keep_alive, daemon=True).start()

bot.infinity_polling()
