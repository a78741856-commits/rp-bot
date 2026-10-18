import os
import sqlite3
import telebot
from telebot import types

# Получаем токен из переменных окружения BotHost
TOKEN = os.getenv(8968464316:AAERykZISUAVdpuEkChWDOzejRYccKfdgjU)
# Твой Telegram ID (только ты сможешь использовать глобан)
OWNER_ID = 8765917744  # <--- ЗАМЕНИ НА СВОЙ ID!

bot = telebot.TeleBot(TOKEN)

# Инициализация базы данных SQLite
db = sqlite3.connect("net_bot.db", check_same_thread=False)
cursor = db.cursor()

# Создание таблиц
cursor.execute("""
CREATE TABLE IF NOT EXISTS global_bans (
    user_id INTEGER PRIMARY KEY,
    reason TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS activity (
    user_id INTEGER,
    chat_id INTEGER,
    messages_total INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, chat_id)
)
""")
db.commit()


# --- ПРОВЕРКА НА ГЛОБАЛЬНЫЙ БАН ПРИ КАЖДОМ СООБЩЕНИИ ---
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'voice', 'document', 'audio'])
def handle_all_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # 1. Проверяем, есть ли юзер в глобальном бане
    cursor.execute("SELECT reason FROM global_bans WHERE user_id = ?", (user_id,))
    ban_row = cursor.fetchone()
    if ban_row:
        try:
            # Пытаемся забанить/кикнуть нарушителя в текущем чате
            bot.ban_chat_member(chat_id, user_id)
            bot.delete_message(chat_id, message.message_id)
            return
        except Exception:
            pass  тоже самое, если у бота нет прав админа на кик

    # 2. Учитываем активность пользователя в базе
    cursor.execute("""
        INSERT INTO activity (user_id, chat_id, messages_total) 
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, chat_id) 
        DO UPDATE SET messages_total = messages_total + 1
    """, (user_id, chat_id))
    db.commit()


# --- КОМАНДЫ СОДРУЖЕСТВА ---

# 1. Глобальный бан (Только для тебя)
@bot.message_handler(commands=['global_ban'])
def global_ban(message):
    if message.from_user.id != OWNER_ID:
        return bot.reply_to(message, "❌ У тебя нет прав на эту команду.")

    args = message.text.split(maxsplit=2)
    
    # Если команда вызвана реплаем на сообщение нарушителя
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        reason = args[1] if len(args) > 1 else "Нарушение правил содружества"
    elif len(args) >= 2:
        try:
            target_id = int(args[1])
            reason = args[2] if len(args) > 2 else "Нарушение правил содружества"
        except ValueError:
            return bot.reply_to(message, "❌ Неверный ID пользователя.")
    else:
        return bot.reply_to(message, "Использование: /global_ban [ID] [причина] или ответом на сообщение.")

    # Добавляем в базу глобан
    cursor.execute("INSERT OR REPLACE INTO global_bans (user_id, reason) VALUES (?, ?)", (target_id, reason))
    db.commit()

    bot.reply_to(message, f"🚨 Пользователь <code>{target_id}</code> добавлен в ГЛОБАЛЬНЫЙ БАН.\nПричина: {reason}", parse_mode="HTML")


# 2. Снятие глобального бана
@bot.message_handler(commands=['global_unban'])
def global_unban(message):
    if message.from_user.id != OWNER_ID:
        return

    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Укажи ID: /global_unban [ID]")

    target_id = int(args[1])
    cursor.execute("DELETE FROM global_bans WHERE user_id = ?", (target_id,))
    db.commit()
    bot.reply_to(message, f"✅ Пользователь {target_id} помилован и удален из глобального бана.")


# 3. Проверка своей или чужой статистики (/stats)
@bot.message_handler(commands=['stats'])
def get_stats(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    cursor.execute("SELECT messages_total FROM activity WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
    row = cursor.fetchone()
    msgs = row[0] if row else 0

    # Считаем общую активность юзера во ВСЕЙ сетке
    cursor.execute("SELECT SUM(messages_total) FROM activity WHERE user_id = ?", (user_id,))
    total_row = cursor.fetchone()
    net_msgs = total_row[0] if total_row and total_row[0] else 0

    bot.reply_to(message, 
        f"📊 Статистика пользователя:\n"
        f"💬 Сообщений в этом чате: {msgs}\n"
        f"🌐 Сообщений во всей сетке (18 проектов): {net_msgs}"
    )


# Запуск бота
if name == "main":
    print("Бот Содружества запущен!")
    bot.infinity_polling(skip_pending=True)
