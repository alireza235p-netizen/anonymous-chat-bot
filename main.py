import os
import logging
from collections import defaultdict, deque

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI


# ═══════════════════════════════════════
# ⚙️ تنظیمات
# ═══════════════════════════════════════

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

client = OpenAI(
    api_key=OPENAI_API_KEY
)


# ═══════════════════════════════════════
# 🧠 حافظه کاربران
# ═══════════════════════════════════════

ai_memory = defaultdict(
    lambda: deque(maxlen=12)
)

ai_mode = set()

# زبان کاربران
user_languages = {}

# پروفایل کاربران
user_profiles = {}


# ═══════════════════════════════════════
# 🌍 زبان‌ها
# ═══════════════════════════════════════

LANGUAGES = {
    "fa": "🇮🇷 فارسی",
    "en": "🇬🇧 English",
    "ar": "🇸🇦 العربية",
    "tr": "🇹🇷 Türkçe",
    "ru": "🇷🇺 Русский",
    "es": "🇪🇸 Español",
    "fr": "🇫🇷 Français",
    "de": "🇩🇪 Deutsch",
    "hi": "🇮🇳 हिन्दी",
    "zh": "🇨🇳 中文",
}


# ═══════════════════════════════════════
# 📝 متن‌های زبان
# ═══════════════════════════════════════

TEXTS = {

    "en": {
        "welcome": "✨ Welcome {name}! 🤖\n\nI'm your smart AI assistant.\n\n💬 Chat with AI\n🧠 Ask questions\n📚 Learn and study\n💻 Programming help\n🎵 Music assistance\n🎬 Movie discovery\n🖼️ Image assistance\n🔗 Link analysis\n✍️ Writing and translation\n💡 Ideas and creativity\n\n🌍 Please choose your language to continue:",
        "profile": "👤 Your Profile\n\n🆔 User ID: {id}\n🌍 Language: {language}\n💬 AI chats: {chats}\n\n✨ Your smart assistant profile",
        "language_changed": "✅ Language changed successfully!",
        "choose_language": "🌍 Choose your language:",
        "ai_ready": "🤖 AI Assistant is ready!\n\nSend me anything you want to ask.",
        "restart": "🔄 Welcome back, {name}!",
    },

    "fa": {
        "welcome": "✨ سلام {name}! 🤖\n\nبه دستیار هوشمند همه‌کاره خوش اومدی! 🚀\n\n💬 گفت‌وگوی هوشمند\n🧠 پاسخ به سؤالات\n📚 کمک در درس و تحقیق\n💻 برنامه‌نویسی\n🎵 کمک برای موسیقی\n🎬 پیدا کردن فیلم\n🖼️ کمک در زمینه عکس\n🔗 تحلیل لینک\n✍️ نوشتن و ترجمه\n💡 ایده‌پردازی\n\n🌍 زبانت رو انتخاب کن:",
        "profile": "👤 پروفایل من\n\n🆔 شناسه: {id}\n🌍 زبان: {language}\n💬 تعداد گفتگوهای AI: {chats}\n\n✨ پروفایل دستیار هوشمند شما",
        "language_changed": "✅ زبان با موفقیت تغییر کرد!",
        "choose_language": "🌍 زبان موردنظرت رو انتخاب کن:",
        "ai_ready": "🤖 دستیار هوشمند آماده‌ست!\n\nهر چیزی می‌خوای بپرس، من در خدمتم. ✨",
        "restart": "🔄 خوش برگشتی {name}!",
    },

    "ar": {
        "welcome": "✨ مرحباً {name}! 🤖\n\nأنا مساعدك الذكي متعدد الاستخدامات! 🚀\n\n💬 محادثة ذكية\n🧠 الإجابة على الأسئلة\n📚 المساعدة في الدراسة\n💻 البرمجة\n🎵 الموسيقى\n🎬 الأفلام\n🖼️ الصور\n🔗 تحليل الروابط\n✍️ الكتابة والترجمة\n💡 الأفكار والإبداع\n\n🌍 اختر لغتك:",
        "profile": "👤 ملفك الشخصي\n\n🆔 المعرف: {id}\n🌍 اللغة: {language}\n💬 محادثات AI: {chats}",
        "language_changed": "✅ تم تغيير اللغة بنجاح!",
        "choose_language": "🌍 اختر لغتك:",
        "ai_ready": "🤖 المساعد الذكي جاهز!\n\nأرسل لي أي سؤال.",
        "restart": "🔄 أهلاً بعودتك {name}!",
    },
}


# ═══════════════════════════════════════
# 🌍 دریافت زبان کاربر
# ═══════════════════════════════════════

def get_language(user_id):

    return user_languages.get(
        user_id,
        "en"
    )


def get_text(user_id, key):

    lang = get_language(user_id)

    language_texts = TEXTS.get(
        lang,
        TEXTS["en"]
    )

    return language_texts.get(
        key,
        TEXTS["en"].get(key, "")
    )


# ═══════════════════════════════════════
# 🌍 منوی انتخاب زبان
# ═══════════════════════════════════════

def language_keyboard():

    buttons = []

    for code, name in LANGUAGES.items():

        buttons.append(
            [
                InlineKeyboardButton(
                    name,
                    callback_data=f"lang_{code}"
                )
            ]
        )

    return InlineKeyboardMarkup(
        buttons
    )


# ═══════════════════════════════════════
# 🎨 منوی اصلی
# ═══════════════════════════════════════

def main_keyboard(user_id):

    lang = get_language(user_id)

    if lang == "fa":

        keyboard = [

            [
                KeyboardButton("🤖 گفت‌وگو با AI"),
                KeyboardButton("🧠 ابزارهای هوشمند"),
            ],

            [
                KeyboardButton("👤 پروفایل من"),
                KeyboardButton("🌍 تغییر زبان"),
            ],

            [
                KeyboardButton("🎵 تشخیص آهنگ"),
                KeyboardButton("🎬 پیدا کردن فیلم"),
            ],

            [
                KeyboardButton("🖼️ بهبود عکس"),
                KeyboardButton("🔗 تحلیل لینک"),
            ],

            [
                KeyboardButton("🔄 شروع دوباره"),
            ],

        ]

    else:

        keyboard = [

            [
                KeyboardButton("🤖 Chat with AI"),
                KeyboardButton("🧠 Smart Tools"),
            ],

            [
                KeyboardButton("👤 My Profile"),
                KeyboardButton("🌍 Change Language"),
            ],

            [
                KeyboardButton("🎵 Music Finder"),
                KeyboardButton("🎬 Movie Finder"),
            ],

            [
                KeyboardButton("🖼️ Image Tools"),
                KeyboardButton("🔗 Link Analysis"),
            ],

            [
                KeyboardButton("🔄 Restart"),
            ],

        ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


# ═══════════════════════════════════════
# 👋 شروع
# ═══════════════════════════════════════

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    user_id = user.id

    if user_id not in user_profiles:

        user_profiles[user_id] = {
            "name": user.first_name or "User",
            "chats": 0,
        }

    text = get_text(
        user_id,
        "welcome"
    ).format(
        name=user.first_name or "Friend"
    )

    await update.message.reply_text(
        text,
        reply_markup=language_keyboard()
    )


# ═══════════════════════════════════════
# 🌍 انتخاب زبان
# ═══════════════════════════════════════

async def language_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    lang_code = query.data.replace(
        "lang_",
        ""
    )

    if lang_code not in LANGUAGES:
        return

    user_languages[user_id] = lang_code

    await query.edit_message_text(

        get_text(
            user_id,
            "language_changed"
        )

    )

    await context.bot.send_message(

        chat_id=user_id,

        text=get_text(
            user_id,
            "restart"
        ).format(
            name=query.from_user.first_name or "Friend"
        ),

        reply_markup=main_keyboard(
            user_id
        )

    )


# ═══════════════════════════════════════
# 👤 پروفایل جدید
# ═══════════════════════════════════════

async def profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    profile_data = user_profiles.get(
        user_id,
        {
            "name": update.effective_user.first_name or "User",
            "chats": 0,
        }
    )

    language = LANGUAGES.get(
        get_language(user_id),
        "English"
    )

    text = get_text(
        user_id,
        "profile"
    ).format(

        id=user_id,

        language=language,

        chats=profile_data.get(
            "chats",
            0
        )

    )

    await update.message.reply_text(

        "╭━━━━━━━━━━━━━━╮\n"
        "      👤 PROFILE\n"
        "╰━━━━━━━━━━━━━━╯\n\n"
        + text
        + "\n\n"
        "✨ Your AI journey starts here.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# ═══════════════════════════════════════
# 🤖 شروع AI
# ═══════════════════════════════════════

async def start_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    ai_mode.add(
        user_id
    )

    ai_memory[user_id].clear()

    await update.message.reply_text(

        get_text(
            user_id,
            "ai_ready"
        ),

        reply_markup=main_keyboard(
            user_id
        )

    )


# ═══════════════════════════════════════
# 🧠 ارسال پیام به OpenAI
# ═══════════════════════════════════════

async def ask_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    text = update.message.text

    if not text:
        return

    language = LANGUAGES.get(
        get_language(user_id),
        "English"
    )

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
                "You are a professional multilingual AI assistant. "
                f"The user's selected language is {language}. "
                "Always answer in the user's selected language. "
                "Be helpful, clear, friendly and concise. "
                "You can help with education, programming, writing, "
                "translation, movies, music, images, links and general questions."
            )
        }

    ]

    messages.extend(
        list(
            ai_memory[user_id]
        )
    )

    try:

        response = client.responses.create(

            model="gpt-4o-mini",

            input=messages

        )

        answer = response.output_text

        if not answer:

            answer = "❌ No response received."

        ai_memory[user_id].append(

            {
                "role": "assistant",
                "content": answer
            }

        )

        if user_id in user_profiles:

            user_profiles[user_id][
                "chats"
            ] += 1

        await update.message.reply_text(

            answer,

            reply_markup=main_keyboard(
                user_id
            )

        )

    except Exception as error:

        logging.exception(
            "OPENAI_ERROR"
        )

        await update.message.reply_text(

            f"❌ OpenAI Error:\n\n"
            f"{type(error).__name__}\n\n"
            f"{str(error)}",

            reply_markup=main_keyboard(
                user_id
            )

        )


# ═══════════════════════════════════════
# 🧠 ابزارهای هوشمند
# ═══════════════════════════════════════

async def smart_tools(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    await update.message.reply_text(

        "🧠 Smart Tools\n\n"
        "🎵 Music identification\n"
        "🎬 Movie discovery\n"
        "🖼️ Image assistance\n"
        "🔗 Link analysis\n"
        "✍️ Writing and translation\n"
        "💻 Programming\n"
        "📚 Education\n\n"
        "🚀 More tools coming soon!",

        reply_markup=main_keyboard(
            user_id
        )

    )


# ═══════════════════════════════════════
# 🎵 موسیقی
# ═══════════════════════════════════════

async def music_finder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    await update.message.reply_text(

        "🎵 Music Finder\n\n"
        "Send me the song name, artist or lyrics.\n\n"
        "🔜 Audio/video recognition will be added with a music API.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# ═══════════════════════════════════════
# 🎬 فیلم
# ═══════════════════════════════════════

async def movie_finder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    await update.message.reply_text(

        "🎬 Movie Finder\n\n"
        "Tell me anything you remember about the movie.\n"
        "Name, actor, story or scene.\n\n"
        "I'll help you find it.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# ═══════════════════════════════════════
# 🖼️ عکس
# ═══════════════════════════════════════

async def improve_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    await update.message.reply_text(

        "🖼️ Image Tools\n\n"
        "Send an image and describe what you want.\n\n"
        "✨ Improve quality\n"
        "🧹 Remove background\n"
        "🎨 Change style\n"
        "💡 Improve lighting\n\n"
        "🔜 Image editing API can be connected here.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# ═══════════════════════════════════════
# 🔗 لینک
# ═══════════════════════════════════════

async def analyze_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    await update.message.reply_text(

        "🔗 Link Analysis\n\n"
        "Send me a link and I'll help analyze it.\n\n"
        "📱 Instagram\n"
        "🎵 Music\n"
        "🎬 Video\n"
        "📝 Web pages\n\n"
        "🚀 More link tools can be connected later.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# ═══════════════════════════════════════
# 🔄 شروع دوباره
# ═══════════════════════════════════════

async def restart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    ai_mode.discard(
        user_id
    )

    ai_memory[user_id].clear()

    await start(
        update,
        context
    )


# ═══════════════════════════════════════
# 📨 پردازش پیام‌ها
# ═══════════════════════════════════════

async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    user_id = update.effective_user.id

    if text == "🤖 گفت‌وگو با AI" or text == "🤖 Chat with AI":

        await start_ai(
            update,
            context
        )

        return

    if text == "🧠 ابزارهای هوشمند" or text == "🧠 Smart Tools":

        await smart_tools(
            update,
            context
        )

        return

    if text == "👤 پروفایل من" or text == "👤 My Profile":

        await profile(
            update,
            context
        )

        return

    if text == "🌍 تغییر زبان" or text == "🌍 Change Language":

        await update.message.reply_text(

            get_text(
                user_id,
                "choose_language"
            ),

            reply_markup=language_keyboard()

        )

        return

    if text == "🎵 تشخیص آهنگ" or text == "🎵 Music Finder":

        await music_finder(
            update,
            context
        )

        return

    if text == "🎬 پیدا کردن فیلم" or text == "🎬 Movie Finder":

        await movie_finder(
            update,
            context
        )

        return

    if text == "🖼️ بهبود عکس" or text == "🖼️ Image Tools":

        await improve_photo(
            update,
            context
        )

        return

    if text == "🔗 تحلیل لینک" or text == "🔗 Link Analysis":

        await analyze_link(
            update,
            context
        )

        return

    if text == "🔄 شروع دوباره" or text == "🔄 Restart":

        await restart(
            update,
            context
        )

        return

    if user_id in ai_mode:

        await ask_ai(
            update,
            context
        )

        return

    await update.message.reply_text(

        "👇 Please choose an option from the menu.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# ═══════════════════════════════════════
# 🚀 اجرای ربات
# ═══════════════════════════════════════

def main():

    app = (

        Application

        .builder()

        .token(
            BOT_TOKEN
        )

        .build()

    )

    app.add_handler(

        CommandHandler(
            "start",
            start
        )

    )

    app.add_handler(

        CallbackQueryHandler(
            language_callback,
            pattern="^lang_"
        )

    )

    app.add_handler(

        MessageHandler(

            filters.TEXT
            & ~filters.COMMAND,

            handle_text

        )

    )

    print(
        "🤖 Smart Multilingual AI Assistant is running..."
    )

    app.run_polling()


if __name__ == "__main__":

    main()
