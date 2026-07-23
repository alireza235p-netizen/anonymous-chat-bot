import os
import logging
from collections import defaultdict, deque

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI


# =========================
# تنظیمات
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN تنظیم نشده است")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY تنظیم نشده است")

client = OpenAI(api_key=OPENAI_API_KEY)


# =========================
# حافظه موقت گفتگو
# =========================

ai_memory = defaultdict(lambda: deque(maxlen=10))
ai_mode = set()


# =========================
# منوی اصلی
# =========================

def main_keyboard():

    keyboard = [
        [
            KeyboardButton("🤖 چت با هوش مصنوعی"),
            KeyboardButton("🎲 جستجوی شانسی"),
        ],
        [
            KeyboardButton("💬 نفر بعدی"),
            KeyboardButton("🛑 پایان گفتگو"),
        ],
        [
            KeyboardButton("👤 پروفایل من"),
            KeyboardButton("🪙 موجودی سکه"),
        ],
        [
            KeyboardButton("❤️ لایک‌ها"),
            KeyboardButton("👥 دعوت دوستان"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


# =========================
# شروع
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🌈 سلام!\n\n"
        "🤖 به ربات خوش اومدی.\n\n"
        "از منوی پایین انتخاب کن:",
        reply_markup=main_keyboard()
    )


# =========================
# ورود به چت AI
# =========================

async def start_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    ai_mode.add(user_id)

    ai_memory[user_id].clear()

    await update.message.reply_text(
        "🤖 چت با هوش مصنوعی فعال شد!\n\n"
        "💬 هر چیزی می‌خوای بپرس.\n"
        "🧠 من چند پیام اخیر مکالمه رو به خاطر می‌سپارم.\n\n"
        "برای خروج از حالت AI بنویس:\n"
        "🔙 خروج",
        reply_markup=main_keyboard()
    )


# =========================
# خروج از AI
# =========================

async def stop_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    ai_mode.discard(user_id)
    ai_memory[user_id].clear()

    await update.message.reply_text(
        "✅ از چت هوش مصنوعی خارج شدی.",
        reply_markup=main_keyboard()
    )


# =========================
# ارسال پیام به AI
# =========================

async def ask_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id
    text = update.message.text

    if not text:
        return

    ai_memory[user_id].append(
        {
            "role": "user",
            "content": text
        }
    )

    messages = [
        {
            "role": "system",
            "content": (
                "تو یک دستیار هوش مصنوعی دوستانه و مفید هستی. "
                "به زبان کاربر پاسخ بده. "
                "پاسخ‌ها را واضح و قابل فهم ارائه کن."
            )
        }
    ]

    messages.extend(
        list(ai_memory[user_id])
    )

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=700
        )

        answer = response.choices[0].message.content

        ai_memory[user_id].append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        await update.message.reply_text(
            answer,
            reply_markup=main_keyboard()
        )

    except Exception as error:

        logging.error(error)

        await update.message.reply_text(
            "❌ متأسفانه در اتصال به هوش مصنوعی مشکلی پیش آمد."
        )


# =========================
# پردازش پیام‌ها
# =========================

async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text
    user_id = update.effective_user.id

    if text == "🤖 چت با هوش مصنوعی":

        await start_ai(update, context)
        return

    if text == "🔙 خروج":

        await stop_ai(update, context)
        return

    if user_id in ai_mode:

        await ask_ai(update, context)
        return

    await update.message.reply_text(
        "👇 از منوی پایین انتخاب کن:",
        reply_markup=main_keyboard()
    )


# =========================
# اجرای ربات
# =========================

def main():

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    print(
        "🤖 Telegram AI Bot is running..."
    )

    app.run_polling()


if __name__ == "__main__":

    main()
