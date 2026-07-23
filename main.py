import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

waiting_users = []
active_chats = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    text = (
        f"👋 سلام {user.first_name}\n\n"
        "🤖 به ربات چت ناشناس خوش اومدی.\n\n"
        "دستورات:\n"
        "/find - پیدا کردن مخاطب\n"
        "/next - نفر بعدی\n"
        "/stop - قطع گفتگو"
    )

    await update.message.reply_text(text)


async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in active_chats:
        await update.message.reply_text(
            "❗️شما همین الان داخل گفتگو هستید."
        )
        return

    if waiting_users and waiting_users[0] != user_id:
        partner = waiting_users.pop(0)

        active_chats[user_id] = partner
        active_chats[partner] = user_id

        await context.bot.send_message(
            user_id,
            "✅ مخاطب پیدا شد. حالا می‌توانید پیام ارسال کنید."
        )

        await context.bot.send_message(
            partner,
            "✅ مخاطب پیدا شد. حالا می‌توانید پیام ارسال کنید."
        )

    else:
        if user_id not in waiting_users:
            waiting_users.append(user_id)

        await update.message.reply_text(
            "⏳ در حال جستجوی مخاطب..."
        )


async def relay_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in active_chats:
        return

    partner = active_chats[user_id]

    try:
        await update.message.copy(chat_id=partner)
    except Exception:
        await update.message.reply_text(
            "❌ ارسال پیام انجام نشد."
        )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in active_chats:
        await update.message.reply_text(
            "❗️شما داخل هیچ گفتگویی نیستید."
        )
        return

    partner = active_chats[user_id]

    del active_chats[user_id]

    if partner in active_chats:
        del active_chats[partner]

        await context.bot.send_message(
            partner,
            "🔚 طرف مقابل گفتگو را قطع کرد."
        )

    await update.message.reply_text(
        "✅ گفتگو پایان یافت."
    )


async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in active_chats:
        partner = active_chats[user_id]

        del active_chats[user_id]

        if partner in active_chats:
            del active_chats[partner]

            await context.bot.send_message(
                partner,
                "🔚 طرف مقابل گفتگو را قطع کرد."
            )

    await find(update, context)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("find", find))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("next", next_chat))

    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            relay_message
        )
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
