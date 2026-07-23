import os
import logging
import random
import math
from datetime import datetime, timezone

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from supabase import create_client, Client


# ═══════════════════════════════════════
# ⚙️ تنظیمات
# ═══════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN تنظیم نشده است")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL یا SUPABASE_KEY تنظیم نشده است")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ═══════════════════════════════════════
# 🧠 وضعیت موقت بات
# ═══════════════════════════════════════

waiting_users = []
active_chats = {}
chat_started_at = {}


# ═══════════════════════════════════════
# 🎨 منوی اصلی
# ═══════════════════════════════════════

def main_keyboard():
    keyboard = [
        [
            KeyboardButton("🔍 جستجوی هوشمند"),
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
        [
            KeyboardButton("💰 کسب درآمد"),
            KeyboardButton("⚙️ تنظیمات"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


# ═══════════════════════════════════════
# 👤 ساخت یا دریافت کاربر
# ═══════════════════════════════════════

def get_user(user_id):

    result = (
        supabase
        .table("users")
        .select("*")
        .eq("id", user_id)
        .execute()
    )

    if result.data:
        return result.data[0]

    new_user = {
        "id": user_id,
        "username": "",
        "first_name": "",
        "coins": 0,
        "likes": 0,
        "referrals": 0,
        "last_seen": datetime.now(timezone.utc).isoformat()
    }

    try:
        supabase.table("users").insert(new_user).execute()
        return new_user
    except Exception:
        return None


# ═══════════════════════════════════════
# 🪙 تغییر موجودی سکه
# ═══════════════════════════════════════

def change_coins(user_id, amount, transaction_type, description):

    user = get_user(user_id)

    if not user:
        return False

    current_coins = user.get("coins") or 0
    new_coins = current_coins + amount

    if new_coins < 0:
        return False

    (
        supabase
        .table("users")
        .update({"coins": new_coins})
        .eq("id", user_id)
        .execute()
    )

    transaction = {
        "user_id": user_id,
        "amount": amount,
        "type": transaction_type,
        "description": description
    }

    supabase.table("coin_transactions").insert(
        transaction
    ).execute()

    return True


# ═══════════════════════════════════════
# 🚀 شروع
# ═══════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    get_user(user.id)

    await update.message.reply_text(
        f"🌈 سلام {user.first_name} عزیز! 😍\n\n"
        "🎉 به دنیای چت ناشناس خوش اومدی!\n\n"
        "💬 اینجا می‌تونی با آدم‌های جدید آشنا بشی.\n"
        "🎲 جستجوی شانسی کاملاً رایگانه!\n"
        "🪙 برای بعضی اتصال‌ها سکه مصرف میشه.\n\n"
        "👇 از منوی پایین انتخاب کن:",
        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🪙 موجودی
# ═══════════════════════════════════════

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    coins = user.get("coins", 0) if user else 0

    await update.message.reply_text(
        f"🪙 موجودی شما:\n\n"
        f"✨ {coins} سکه\n\n"
        "💡 با دعوت دوستان می‌تونی سکه رایگان بگیری!",
        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 👤 پروفایل
# ═══════════════════════════════════════

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    if not user:
        await update.message.reply_text(
            "❌ خطایی در دریافت پروفایل رخ داد."
        )
        return

    age = user.get("age") or "ثبت نشده"
    city = user.get("city") or "ثبت نشده"
    province = user.get("province") or "ثبت نشده"
    likes = user.get("likes") or 0
    coins = user.get("coins") or 0

    await update.message.reply_text(
        "👤 پروفایل شما\n\n"
        f"🎂 سن: {age}\n"
        f"📍 استان: {province}\n"
        f"🏙️ شهر: {city}\n"
        f"❤️ لایک‌ها: {likes}\n"
        f"🪙 سکه: {coins}\n\n"
        "برای تکمیل پروفایل، در نسخه بعدی اطلاعات بیشتری اضافه می‌کنیم.",
        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🎲 جستجوی شانسی
# ═══════════════════════════════════════

async def random_search(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id in active_chats:
        await update.message.reply_text(
            "❗️شما الان داخل یک گفتگو هستید."
        )
        return

    if user_id in waiting_users:
        await update.message.reply_text(
            "⏳ شما از قبل در صف جستجو هستید."
        )
        return

    if waiting_users:

        partner = random.choice(waiting_users)
        waiting_users.remove(partner)

        active_chats[user_id] = partner
        active_chats[partner] = user_id

        now = datetime.now(timezone.utc)

        chat_started_at[user_id] = now
        chat_started_at[partner] = now

        await context.bot.send_message(
            user_id,
            "🎉 مخاطب پیدا شد!\n\n"
            "💬 حالا می‌تونید ناشناس با هم صحبت کنید.\n"
            "⏱️ حداقل ۱۲ ثانیه فرصت دارید.\n\n"
            "🛑 پایان گفتگو\n"
            "🔄 نفر بعدی",
            reply_markup=main_keyboard()
        )

        await context.bot.send_message(
            partner,
            "🎉 مخاطب پیدا شد!\n\n"
            "💬 حالا می‌تونید ناشناس با هم صحبت کنید.\n"
            "⏱️ حداقل ۱۲ ثانیه فرصت دارید.\n\n"
            "🛑 پایان گفتگو\n"
            "🔄 نفر بعدی",
            reply_markup=main_keyboard()
        )

    else:

        waiting_users.append(user_id)

        await update.message.reply_text(
            "🔎 در حال پیدا کردن یک مخاطب ناشناس...\n\n"
            "🎲 جستجوی شانسی رایگانه!\n"
            "⏳ کمی صبر کن...",
            reply_markup=main_keyboard()
        )


# ═══════════════════════════════════════
# 🛑 پایان گفتگو
# ═══════════════════════════════════════

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in active_chats:

        if user_id in waiting_users:
            waiting_users.remove(user_id)

        await update.message.reply_text(
            "❗️شما داخل گفتگویی نیستید.",
            reply_markup=main_keyboard()
        )

        return

    start_time = chat_started_at.get(user_id)

    if start_time:

        elapsed = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()

        if elapsed < 12:

            remaining = int(12 - elapsed)

            await update.message.reply_text(
                f"⏱️ هنوز {remaining} ثانیه از شروع گفتگو نگذشته!\n"
                "لطفاً کمی صبر کن 😄"
            )

            return

    partner = active_chats[user_id]

    del active_chats[user_id]

    chat_started_at.pop(user_id, None)

    if partner in active_chats:

        del active_chats[partner]

        chat_started_at.pop(partner, None)

        await context.bot.send_message(
            partner,
            "🔚 طرف مقابل گفتگو را پایان داد.\n\n"
            "🎲 برای پیدا کردن نفر جدید، جستجوی شانسی را بزن!",
            reply_markup=main_keyboard()
        )

    await update.message.reply_text(
        "✅ گفتگو با موفقیت پایان یافت.\n\n"
        "💬 ممنون که از ربات استفاده کردی!",
        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🔄 نفر بعدی
# ═══════════════════════════════════════

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id in active_chats:

        start_time = chat_started_at.get(user_id)

        if start_time:

            elapsed = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()

            if elapsed < 12:

                await update.message.reply_text(
                    "⏱️ هنوز ۱۲ ثانیه کامل نشده!\n"
                    "کمی دیگه صبر کن 😄"
                )

                return

        partner = active_chats[user_id]

        del active_chats[user_id]

        chat_started_at.pop(user_id, None)

        if partner in active_chats:

            del active_chats[partner]

            chat_started_at.pop(partner, None)

            await context.bot.send_message(
                partner,
                "🔄 طرف مقابل رفت دنبال نفر بعدی.",
                reply_markup=main_keyboard()
            )

    await random_search(update, context)


# ═══════════════════════════════════════
# 💬 انتقال پیام
# ═══════════════════════════════════════

async def relay_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    if user_id not in active_chats:
        return

    partner = active_chats[user_id]

    try:

        await update.message.copy(
            chat_id=partner
        )

    except Exception as error:

        logging.error(error)

        await update.message.reply_text(
            "❌ ارسال پیام انجام نشد."
        )


# ═══════════════════════════════════════
# 👥 دعوت دوستان
# ═══════════════════════════════════════

async def referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    bot = await context.bot.get_me()

    link = (
        f"https://t.me/{bot.username}"
        f"?start=ref_{user_id}"
    )

    user = get_user(user_id)

    count = user.get("referrals", 0) if user else 0

    await update.message.reply_text(
        "👥 دعوت دوستان\n\n"
        f"🎁 به ازای هر دوست جدید: 🪙 ۱۰ سکه\n\n"
        f"👤 تعداد دعوت‌های شما: {count}\n\n"
        "🔗 لینک دعوت شما:\n"
        f"{link}\n\n"
        "📢 لینک رو برای دوستات بفرست!",
        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 💰 کسب درآمد
# ═══════════════════════════════════════

async def earn_money(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "💰 کسب درآمد\n\n"
        "🪙 این بخش برای فروش سکه و سیستم درآمدزایی آماده شده.\n\n"
        "📦 بسته‌های سکه در نسخه بعدی اضافه می‌شن.\n"
        "💳 پرداخت آنلاین هم بعداً قابل اتصال هست.",
        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# ❤️ لایک‌ها
# ═══════════════════════════════════════

async def likes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    count = user.get("likes", 0) if user else 0

    await update.message.reply_text(
        f"❤️ تعداد لایک‌های پروفایل شما:\n\n"
        f"💖 {count} لایک",
        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🧠 جستجوی هوشمند
# ═══════════════════════════════════════

async def smart_search(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🧠 جستجوی هوشمند\n\n"
        "🎂 حداقل سن\n"
        "🎂 حداکثر سن\n"
        "👨 پسر\n"
        "👩 دختر\n"
        "🌍 همه\n"
        "📍 انتخاب شهر\n\n"
        "این بخش در مرحله بعدی با دکمه‌های انتخابی تکمیل می‌شود.",
        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# ⚙️ تنظیمات
# ═══════════════════════════════════════

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "⚙️ تنظیمات\n\n"
        "🔔 اعلان‌ها\n"
        "👤 ویرایش پروفایل\n"
        "🔒 حریم خصوصی\n"
        "🚫 کاربران بلاک‌شده",
        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 📨 پردازش دکمه‌ها
# ═══════════════════════════════════════

async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    if text == "🎲 جستجوی شانسی":
        await random_search(update, context)

    elif text == "💬 نفر بعدی":
        await next_chat(update, context)

    elif text == "🛑 پایان گفتگو":
        await stop_chat(update, context)

    elif text == "🪙 موجودی سکه":
        await balance(update, context)

    elif text == "👤 پروفایل من":
        await profile(update, context)

    elif text == "👥 دعوت دوستان":
        await referrals(update, context)

    elif text == "💰 کسب درآمد":
        await earn_money(update, context)

    elif text == "❤️ لایک‌ها":
        await likes(update, context)

    elif text == "🧠 جستجوی هوشمند":
        await smart_search(update, context)

    elif text == "⚙️ تنظیمات":
        await settings(update, context)

    else:
        await relay_message(update, context)


# ═══════════════════════════════════════
# 🚀 اجرای بات
# ═══════════════════════════════════════

def main():

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("find", random_search)
    )

    app.add_handler(
        CommandHandler("stop", stop_chat)
    )

    app.add_handler(
        CommandHandler("next", next_chat)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    app.add_handler(
        MessageHandler(
            ~filters.COMMAND & ~filters.TEXT,
            relay_message
        )
    )

    print("🤖 Anonymous Chat Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
