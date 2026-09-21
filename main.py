import telebot
import google.generativeai as genai

# 1. Твои ключи и ID:
BOT_TOKEN = "8629229178:AAE28GmtJNSVkDvN9btG3Ok-551OabK3mBI"
GEMINI_KEY = "AQ.Ab8RN6LTZS-s0acTl3EwtGFsg2NKKiUNYTe6kryuqQT1v39pwA"
MY_ID = 8765917744  # Твой цифровой ID от @userinfobot (без кавычек)

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)

DATA_FILE = "rp_posts.txt"

PROMPT = """
Ты — судья и аналитик в военно-политической ролевой игре (ВПИ).
Твоя задача — прочитать посты игрока за день и сделать краткий отчёт по категориям:
- 🏛 Внутренняя политика:
- 💰 Экономика:
- ⚔️ Армия и военные действия:
- 🤝 Дипломатия:

Пиши кратко и строго по фактам. Если действий в сфере не было, пиши "Нет изменений".
"""

# Сохранение постов из твоего канала
@bot.channel_post_handler(content_types=['text'])
def save_channel_post(message):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(message.text + "\n---\n")

# Команда /itogi в личке у бота
@bot.message_handler(commands=['itogi'])
def give_summary(message):
    if message.from_user.id != MY_ID:
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            posts = f.read().strip()
    except FileNotFoundError:
        posts = ""

    if not posts:
        bot.send_message(message.chat.id, "За сегодня постов пока нет!")
        return

    bot.send_message(message.chat.id, "⏳ Анализирую посты за день...")

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"{PROMPT}\n\nПосты игрока за день:\n{posts}")
        bot.send_message(message.chat.id, response.text)

        # Очищаем файл для нового дня
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write("")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")

bot.infinity_polling()
