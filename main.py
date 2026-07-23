import logging
import os
from collections import defaultdict

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

# ==================================================
# ⚙️ تنظیمات اصلی
# ==================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# کاربران منتظر برای پیدا کردن مخاطب
waiting_users = []

# چت‌های فعال
active_chats = {}

# کاربران مسدودشده
blocked_users = defaultdict(set)

# تعداد چت‌های کاربران
user_stats = defaultdict(int)


# ==================================================
# 🎨 منوی اصلی
# ==================================================

def main_keyboard():

    keyboard = [
        [
            KeyboardButton("🔍 جستجوی مخاطب"),
        ],
        [
            KeyboardButton("⏭️ مخاطب بعدی"),
            KeyboardButton("🛑 پایان گفتگو"),
        ],
        [
            KeyboardButton("👤 پروفایل من"),
            KeyboardButton("📊 آمار من"),
        ],
        [
            KeyboardButton("🆘 راهنما"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
    )


# ==================================================
# 🎨 منوی داخل گفتگو
# ==================================================

def chat_keyboard():

    keyboard = [
        [
            KeyboardButton("⏭️ مخاطب بعدی"),
            KeyboardButton("🛑 پایان گفتگو"),
        ],
        [
            KeyboardButton("🚫 مسدود کردن"),
            KeyboardButton("⚠️ گزارش مخاطب"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
    )


# ==================================================
# 🚀 شروع ربات
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    first_name = update.effective_user.first_name

    # حذف از صف
    if user_id in waiting_users:
        waiting_users.remove(user_id)

    # قطع چت قبلی
    if user_id in active_chats:

        partner = active_chats.pop(user_id, None)

        if partner:

            active_chats.pop(partner, None)

            try:
                await context.bot.send_message(
                    partner,
                    "🔚 طرف مقابل دوباره ربات را باز کرد.\n"
                    "گفتگو به پایان رسید.",
                    reply_markup=main_keyboard(),
                )
            except Exception:
                pass

    welcome_text = f"""
╭━━━━━━━━━━━━━━━━━━╮
      🕵️‍♂️ چت ناشناس
╰━━━━━━━━━━━━━━━━━━╯

👋 سلام {first_name}!

🤫 اینجا می‌تونی با افراد مختلف به‌صورت ناشناس گفتگو کنی.

✨ ویژگی‌های ربات:

💬 گفتگوی کاملاً ناشناس
🔎 پیدا کردن افراد تصادفی
⏭️ امکان تغییر مخاطب
🚫 امکان مسدود کردن
⚠️ امکان گزارش کاربران

━━━━━━━━━━━━━━━━━━

👇 برای شروع روی دکمه زیر بزن:

🔍 جستجوی مخاطب
"""

    await update.message.reply_text(
        welcome_text,
        reply_markup=main_keyboard(),
    )


# ==================================================
# 🔍 پیدا کردن مخاطب
# ==================================================

async def find_partner(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    # داخل چت
    if user_id in active_chats:

        await update.message.reply_text(
            "⚠️ شما در حال حاضر در یک گفتگو هستید!\n\n"
            "برای تغییر مخاطب از دکمه «⏭️ مخاطب بعدی» استفاده کنید.",
            reply_markup=chat_keyboard(),
        )

        return

    # قبلاً در صف
    if user_id in waiting_users:

        await update.message.reply_text(
            "⏳ شما همین الان در صف جستجو هستید.\n\n"
            "منتظر باشید تا یک مخاطب پیدا شود... 🔎",
            reply_markup=main_keyboard(),
        )

        return

    # پیدا کردن نفر مناسب
    partner = None

    while waiting_users:

        candidate = waiting_users.pop(0)

        if candidate == user_id:
            continue

        # اگر طرف مقابل کاربر را بلاک کرده باشد
        if user_id in blocked_users[candidate]:
            continue

        # اگر کاربر طرف مقابل را بلاک کرده باشد
        if candidate in blocked_users[user_id]:
            continue

        partner = candidate
        break

    # اگر مخاطب پیدا شد
    if partner:

        active_chats[user_id] = partner
        active_chats[partner] = user_id

        user_stats[user_id] += 1
        user_stats[partner] += 1

        try:

            await context.bot.send_message(
                user_id,
                """
╭━━━━━━━━━━━━━━━━━━╮
     🎉 مخاطب پیدا شد!
╰━━━━━━━━━━━━━━━━━━╯

🤫 هویت شما برای طرف مقابل مخفی است.

💬 گفتگو را شروع کنید!

✨ محترمانه صحبت کنید و از گفتگو لذت ببرید.
""",
                reply_markup=chat_keyboard(),
            )

            await context.bot.send_message(
                partner,
                """
╭━━━━━━━━━━━━━━━━━━╮
     🎉 مخاطب پیدا شد!
╰━━━━━━━━━━━━━━━━━━╯

🤫 هویت شما برای طرف مقابل مخفی است.

💬 گفتگو را شروع کنید!

✨ محترمانه صحبت کنید و از گفتگو لذت ببرید.
""",
                reply_markup=chat_keyboard(),
            )

        except Exception as error:

            logging.error(error)

            active_chats.pop(user_id, None)
            active_chats.pop(partner, None)

            await update.message.reply_text(
                "❌ اتصال برقرار نشد.\n"
                "لطفاً دوباره تلاش کنید.",
                reply_markup=main_keyboard(),
            )

    # مخاطبی پیدا نشد
    else:

        waiting_users.append(user_id)

        await update.message.reply_text(
            """
╭━━━━━━━━━━━━━━━━━━╮
     🔎 جستجوی مخاطب
╰━━━━━━━━━━━━━━━━━━╯

⏳ در حال پیدا کردن یک نفر برای شما...

👤 شما وارد صف انتظار شدید.

📢 به محض پیدا شدن مخاطب، اطلاع داده می‌شود.

💡 می‌توانید منتظر بمانید یا جستجو را متوقف کنید.
""",
            reply_markup=main_keyboard(),
        )


# ==================================================
# 🛑 پایان گفتگو
# ==================================================

async def stop_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    # اگر در صف است
    if user_id in waiting_users:

        waiting_users.remove(user_id)

        await update.message.reply_text(
            """
🛑 جستجو متوقف شد.

هر وقت خواستی دوباره با افراد جدید آشنا بشی،
روی 🔍 «جستجوی مخاطب» بزن.
""",
            reply_markup=main_keyboard(),
        )

        return

    # اگر چت ندارد
    if user_id not in active_chats:

        await update.message.reply_text(
            "⚠️ شما در حال حاضر در هیچ گفتگویی نیستید.",
            reply_markup=main_keyboard(),
        )

        return

    partner = active_chats.get(user_id)

    active_chats.pop(user_id, None)

    if partner:

        active_chats.pop(partner, None)

        try:

            await context.bot.send_message(
                partner,
                """
🔚 گفتگو به پایان رسید.

👤 طرف مقابل گفتگو را ترک کرد.

اگر دوست داری با یک نفر جدید آشنا بشی،
روی 🔍 «جستجوی مخاطب» بزن.
""",
                reply_markup=main_keyboard(),
            )

        except Exception:
            pass

    await update.message.reply_text(
        """
✅ گفتگو با موفقیت پایان یافت.

💬 ممنون که از چت ناشناس استفاده کردی!
""",
        reply_markup=main_keyboard(),
    )


# ==================================================
# ⏭️ مخاطب بعدی
# ==================================================

async def next_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    if user_id not in active_chats:

        await update.message.reply_text(
            "⚠️ شما در حال حاضر با کسی گفتگو نمی‌کنید.\n\n"
            "ابتدا یک مخاطب پیدا کنید.",
            reply_markup=main_keyboard(),
        )

        return

    partner = active_chats.pop(user_id, None)

    if partner:

        active_chats.pop(partner, None)

        try:

            await context.bot.send_message(
                partner,
                """
⏭️ طرف مقابل به سراغ یک مخاطب جدید رفت.

🔎 گفتگو به پایان رسید.
""",
                reply_markup=main_keyboard(),
            )

        except Exception:
            pass

    await update.message.reply_text(
        """
⏭️ مخاطب قبلی کنار گذاشته شد.

🔎 در حال پیدا کردن یک مخاطب جدید...
""",
        reply_markup=main_keyboard(),
    )

    await find_partner(
        update,
        context,
    )


# ==================================================
# 🚫 مسدود کردن
# ==================================================

async def block_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    if user_id not in active_chats:

        await update.message.reply_text(
            "⚠️ شما در حال حاضر در گفتگویی نیستید.",
            reply_markup=main_keyboard(),
        )

        return

    partner = active_chats.get(user_id)

    if not partner:
        return

    blocked_users[user_id].add(partner)

    active_chats.pop(user_id, None)
    active_chats.pop(partner, None)

    try:

        await context.bot.send_message(
            partner,
            """
🚫 این گفتگو توسط طرف مقابل پایان یافت.

🔎 شما دیگر با این کاربر روبه‌رو نخواهید شد.
""",
            reply_markup=main_keyboard(),
        )

    except Exception:
        pass

    await update.message.reply_text(
        """
🚫 کاربر مسدود شد.

🔚 گفتگو پایان یافت.

از این به بعد تلاش می‌کنیم دوباره به این کاربر متصل نشوید.
""",
        reply_markup=main_keyboard(),
    )


# ==================================================
# ⚠️ گزارش مخاطب
# ==================================================

async def report_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    if user_id not in active_chats:

        await update.message.reply_text(
            "⚠️ شما در حال حاضر در گفتگویی نیستید.",
            reply_markup=main_keyboard(),
        )

        return

    partner = active_chats.get(user_id)

    # پایان گفتگو
    active_chats.pop(user_id, None)

    if partner:
        active_chats.pop(partner, None)

        try:

            await context.bot.send_message(
                partner,
                """
⚠️ گفتگو توسط طرف مقابل گزارش شد.

🔚 این گفتگو پایان یافت.
""",
                reply_markup=main_keyboard(),
            )

        except Exception:
            pass

    await update.message.reply_text(
        """
⚠️ گزارش شما ثبت شد.

🛡️ ممنون که به امن‌تر شدن محیط کمک می‌کنی.

🔚 گفتگو پایان یافت.
""",
        reply_markup=main_keyboard(),
    )


# ==================================================
# 👤 پروفایل
# ==================================================

async def profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user
    user_id = user.id

    chats = user_stats[user_id]

    status = "💬 در حال گفتگو" if user_id in active_chats else "🟢 آزاد"

    await update.message.reply_text(
        f"""
╭━━━━━━━━━━━━━━━━━━╮
       👤 پروفایل من
╰━━━━━━━━━━━━━━━━━━╯

🆔 شناسه کاربری: {user_id}

📊 تعداد گفتگوها: {chats}

📍 وضعیت فعلی: {status}

🤫 هویت شما برای کاربران دیگر نمایش داده نمی‌شود.
""",
        reply_markup=main_keyboard(),
    )


# ==================================================
# 📊 آمار
# ==================================================

async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    chats = user_stats[user_id]

    await update.message.reply_text(
        f"""
╭━━━━━━━━━━━━━━━━━━╮
        📊 آمار من
╰━━━━━━━━━━━━━━━━━━╯

💬 تعداد گفتگوهای شما:

✨ {chats} گفتگو

━━━━━━━━━━━━━━━━━━

🤖 از چت ناشناس لذت ببرید!
""",
        reply_markup=main_keyboard(),
    )


# ==================================================
# 🆘 راهنما
# ==================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        """
╭━━━━━━━━━━━━━━━━━━╮
       🆘 راهنمای چت ناشناس
╰━━━━━━━━━━━━━━━━━━╯

🔍 جستجوی مخاطب
برای پیدا کردن یک شخص تصادفی.

⏭️ مخاطب بعدی
گفتگوی فعلی را پایان می‌دهد و
دنبال شخص جدید می‌گردد.

🛑 پایان گفتگو
گفتگو را به‌طور کامل متوقف می‌کند.

🚫 مسدود کردن
مخاطب فعلی را مسدود می‌کند.

⚠️ گزارش مخاطب
در صورت رفتار نامناسب می‌توانید
مخاطب را گزارش کنید.

━━━━━━━━━━━━━━━━━━

🛡️ لطفاً قوانین و حریم خصوصی دیگران
را رعایت کنید.

🤝 احترام متقابل باعث می‌شود
محیط بهتری برای همه داشته باشیم.
""",
        reply_markup=main_keyboard(),
    )


# ==================================================
# 💬 انتقال پیام
# ==================================================

async def relay_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    if user_id not in active_chats:
        return

    partner = active_chats.get(user_id)

    if not partner:
        return

    try:

        await update.message.copy(
            chat_id=partner
        )

    except Exception as error:

        logging.error(error)

        await update.message.reply_text(
            "❌ ارسال پیام انجام نشد."
        )


# ==================================================
# 🎛️ مدیریت دکمه‌ها
# ==================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    text = update.message.text

    if text == "🔍 جستجوی مخاطب":

        await find_partner(
            update,
            context,
        )

        return

    if text == "⏭️ مخاطب بعدی":

        await next_chat(
            update,
            context,
        )

        return

    if text == "🛑 پایان گفتگو":

        await stop_chat(
            update,
            context,
        )

        return

    if text == "🚫 مسدود کردن":

        await block_user(
            update,
            context,
        )

        return

    if text == "⚠️ گزارش مخاطب":

        await report_user(
            update,
            context,
        )

        return

    if text == "👤 پروفایل من":

        await profile(
            update,
            context,
        )

        return

    if text == "📊 آمار من":

        await stats(
            update,
            context,
        )

        return

    if text == "🆘 راهنما":

        await help_command(
            update,
            context,
        )

        return

    # انتقال پیام عادی
    await relay_message(
        update,
        context,
    )


# ==================================================
# 🚀 اجرای ربات
# ==================================================

def main():

    if not BOT_TOKEN:

        raise ValueError(
            "❌ BOT_TOKEN در Railway تنظیم نشده است."
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
            "next",
            next_chat,
        )
    )

    app.add_handler(
        CommandHandler(
            "stop",
            stop_chat,
        )
    )

    # پیام‌ها
    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            handle_message,
        )
    )

    print(
        "🚀 Anonymous Chat Bot is running..."
    )

    app.run_polling()


# ==================================================
# 🏁 شروع
# ==================================================

if __name__ == "__main__":
    main()
