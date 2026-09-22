import json
import telebot
import requests

BOT_TOKEN = "8629229178:AAE28GmtJNSVkDvN9btG3Ok-551OabK3mBI"
GEMINI_KEY = "AQ.Ab8RN6IU3zwExbMpHv-ZKE2mwTQQ0HAZ9JxBfn0DNitLyKxJcg"
MY_ID = 8765917744

bot = telebot.TeleBot(BOT_TOKEN)
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

def ask_gemini(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{PROMPT}\n\nПосты игрока за день:\n{text}"}
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    data = response.json()
    
    if response.status_code == 200:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    else:
        error_msg = data.get("error", {}).get("message", "Неизвестная ошибка")
        return f"Ошибка API ({response.status_code}): {error_msg}"

@bot.channel_post_handler(content_types=['text'])
def save_channel_post(message):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(message.text + "\n---\n")

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
        summary = ask_gemini(posts)
        bot.send_message(message.chat.id, summary)

        # Очищаем файл для нового дня
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write("")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")

bot.infinity_polling()
