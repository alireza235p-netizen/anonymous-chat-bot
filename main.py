import logging
import os

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# -----------------------------
# تنظیمات
# -----------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# کاربران منتظر
waiting_users = []

# چت‌های فعال
# مثال:
# {123: 456, 456: 123}
active_chats = {}


# -----------------------------
# منوی اصلی
# -----------------------------

def main_keyboard():
    keyboard = [
        [
            KeyboardButton("🔎 پیدا کردن مخاطب"),
        ],
        [
            KeyboardButton("⏭ نفر بعدی"),
            KeyboardButton("🛑 پایان چت"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
    )


# -----------------------------
# شروع ربات
# -----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # اگر قبلاً در صف بوده، دوباره اضافه نشود
    if user_id in waiting_users:
        waiting_users.remove(user_id)

    # اگر چت فعال داشته، قطع شود
    if user_id in active_chats:
        partner = active_chats.pop(user_id)

        if partner in active_chats:
            active_chats.pop(partner)

            try:
                await context.bot.send_message(
                    partner,
                    "🔚 طرف مقابل دوباره ربات را شروع کرد و گفتگو پایان یافت.",
                )
            except Exception:
                pass

    text = (
        "👋 سلام!\n\n"
        "🤖 به ربات چت ناشناس خوش اومدی.\n\n"
        "اینجا می‌تونی به‌صورت ناشناس با یک نفر دیگه چت کنی.\n\n"
        "🔎 برای پیدا کردن مخاطب روی دکمه «پیدا کردن مخاطب» بزن."
    )

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard(),
    )


# -----------------------------
# پیدا کردن مخاطب
# -----------------------------

async def find_partner(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    # اگر داخل چت است
    if user_id in active_chats:
        await update.message.reply_text(
            "❗️شما در حال حاضر با یک نفر در حال گفتگو هستید."
        )
        return

    # اگر قبلاً در صف است
    if user_id in waiting_users:
        await update.message.reply_text(
            "⏳ شما در حال حاضر در صف جستجو هستید."
        )
        return

    # پیدا کردن اولین کاربر معتبر در صف
    partner = None

    while waiting_users:
        candidate = waiting_users.pop(0)

        # جلوگیری از اتصال کاربر به خودش
        if candidate != user_id:
            partner = candidate
            break

    # اگر کسی پیدا شد
    if partner is not None:

        active_chats[user_id] = partner
        active_chats[partner] = user_id

        try:
            await context.bot.send_message(
                partner,
                "🎉 یک مخاطب پیدا شد!\n\n"
                "💬 حالا می‌تونی ناشناس چت کنی.",
                reply_markup=main_keyboard(),
            )

            await context.bot.send_message(
                user_id,
                "🎉 یک مخاطب پیدا شد!\n\n"
                "💬 حالا می‌تونی ناشناس چت کنی.",
                reply_markup=main_keyboard(),
            )

        except Exception:

            # اگر ارسال پیام به مشکل خورد
            active_chats.pop(user_id, None)
            active_chats.pop(partner, None)

            await update.message.reply_text(
                "❌ اتصال برقرار نشد. دوباره تلاش کن."
            )

    # اگر کسی پیدا نشد
    else:

        waiting_users.append(user_id)

        await update.message.reply_text(
            "🔎 در حال جستجوی مخاطب...\n\n"
            "⏳ وقتی یک نفر پیدا بشه، بهت اطلاع می‌دم.",
            reply_markup=main_keyboard(),
        )


# -----------------------------
# پایان چت
# -----------------------------

async def stop_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    # اگر در صف انتظار است
    if user_id in waiting_users:

        waiting_users.remove(user_id)

        await update.message.reply_text(
            "🛑 جستجو متوقف شد.",
            reply_markup=main_keyboard(),
        )

        return

    # اگر چت فعال ندارد
    if user_id not in active_chats:

        await update.message.reply_text(
            "❗️شما در حال حاضر در هیچ گفتگویی نیستید.",
            reply_markup=main_keyboard(),
        )

        return

    # پیدا کردن طرف مقابل
    partner = active_chats.get(user_id)

    # حذف ارتباط
    active_chats.pop(user_id, None)

    if partner is not None:
        active_chats.pop(partner, None)

        try:
            await context.bot.send_message(
                partner,
                "🔚 طرف مقابل گفتگو را پایان داد.",
                reply_markup=main_keyboard(),
            )
        except Exception:
            pass

    await update.message.reply_text(
        "✅ گفتگو با موفقیت پایان یافت.",
        reply_markup=main_keyboard(),
    )


# -----------------------------
# نفر بعدی
# -----------------------------

async def next_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    # اگر در صف است
    if user_id in waiting_users:

        await update.message.reply_text(
            "⏳ هنوز در صف جستجو هستی."
        )

        return

    # اگر چت فعال ندارد
    if user_id not in active_chats:

        await update.message.reply_text(
            "❗️شما در حال حاضر با کسی چت نمی‌کنید.\n"
            "ابتدا روی «🔎 پیدا کردن مخاطب» بزن."
        )

        return

    # طرف مقابل
    partner = active_chats.get(user_id)

    # حذف چت فعلی
    active_chats.pop(user_id, None)

    if partner is not None:
        active_chats.pop(partner, None)

        try:
            await context.bot.send_message(
                partner,
                "⏭ طرف مقابل به نفر بعدی رفت.",
                reply_markup=main_keyboard(),
            )
        except Exception:
            pass

    # اطلاع به کاربر
    await update.message.reply_text(
        "⏭ گفتگو پایان یافت.\n"
        "🔎 در حال پیدا کردن نفر بعدی...",
        reply_markup=main_keyboard(),
    )

    # جستجوی نفر جدید
    await find_partner(update, context)


# -----------------------------
# انتقال پیام‌ها
# -----------------------------

async def relay_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    # اگر کاربر چت فعال ندارد
    if user_id not in active_chats:
        return

    partner = active_chats.get(user_id)

    if partner is None:
        return

    try:

        # انتقال پیام بدون نمایش هویت واقعی فرستنده
        await update.message.copy(
            chat_id=partner
        )

    except Exception as error:

        logging.error(
            f"Error sending message: {error}"
        )

        await update.message.reply_text(
            "❌ ارسال پیام انجام نشد."
        )


# -----------------------------
# مدیریت پیام‌ها و دکمه‌ها
# -----------------------------

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    text = update.message.text

    # دکمه پیدا کردن
    if text == "🔎 پیدا کردن مخاطب":

        await find_partner(
            update,
            context,
        )

        return

    # دکمه نفر بعدی
    if text == "⏭ نفر بعدی":

        await next_chat(
            update,
            context,
        )

        return

    # دکمه پایان چت
    if text == "🛑 پایان چت":

        await stop_chat(
            update,
            context,
        )

        return

    # پیام معمولی
    await relay_message(
        update,
        context,
    )


# -----------------------------
# اجرای ربات
# -----------------------------

def main():

    if not BOT_TOKEN:

        raise ValueError(
            "BOT_TOKEN در Railway تنظیم نشده است."
        )

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # دستورات
    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        CommandHandler(
            "find",
            find_partner,
        )
    )

    app.add_handler(
        CommandHandler(
            "stop",
            stop_chat,
        )
    )

    app.add_handler(
        CommandHandler(
            "next",
            next_chat,
        )
    )

    # پیام‌های متنی و رسانه‌ای
    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            handle_message,
        )
    )

    print(
        "🤖 Anonymous Chat Bot is running..."
    )

    app.run_polling()


# -----------------------------
# شروع برنامه
# -----------------------------

if __name__ == "__main__":
    main()
