import os
import logging
from collections import defaultdict, deque

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
from groq import Groq


# ═══════════════════════════════════════
# ⚙️ تنظیمات
# ═══════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN تنظیم نشده است")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY تنظیم نشده است")

client = Groq(
    api_key=GROQ_API_KEY
)


# ═══════════════════════════════════════
# 🧠 حافظه
# ═══════════════════════════════════════

ai_memory = defaultdict(
    lambda: deque(maxlen=12)
)

ai_mode = set()

user_languages = {}


# ═══════════════════════════════════════
# 🌍 زبان‌ها
# ═══════════════════════════════════════

LANGUAGES = {
    "🇬🇧 English": "English",
    "🇮🇷 فارسی": "Persian",
    "🇸🇦 العربية": "Arabic",
    "🇪🇸 Español": "Spanish",
    "🇫🇷 Français": "French",
    "🇩🇪 Deutsch": "German",
    "🇷🇺 Русский": "Russian",
    "🇹🇷 Türkçe": "Turkish",
    "🇮🇳 हिन्दी": "Hindi",
    "🇨🇳 中文": "Chinese",
}


def language_keyboard():

    keyboard = [
        [
            KeyboardButton("🇬🇧 English"),
            KeyboardButton("🇮🇷 فارسی"),
        ],
        [
            KeyboardButton("🇸🇦 العربية"),
            KeyboardButton("🇪🇸 Español"),
        ],
        [
            KeyboardButton("🇫🇷 Français"),
            KeyboardButton("🇩🇪 Deutsch"),
        ],
        [
            KeyboardButton("🇷🇺 Русский"),
            KeyboardButton("🇹🇷 Türkçe"),
        ],
        [
            KeyboardButton("🇮🇳 हिन्दी"),
            KeyboardButton("🇨🇳 中文"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


# ═══════════════════════════════════════
# 🎨 منوی اصلی
# ═══════════════════════════════════════

def main_keyboard():

    keyboard = [

        [
            KeyboardButton("🤖 AI Chat"),
            KeyboardButton("🧠 Smart Tools"),
        ],

        [
            KeyboardButton("🎵 Music Finder"),
            KeyboardButton("🎬 Movie Finder"),
        ],

        [
            KeyboardButton("🖼️ Improve Photo"),
            KeyboardButton("🔗 Analyze Link"),
        ],

        [
            KeyboardButton("👤 My Profile"),
            KeyboardButton("🌍 Change Language"),
        ],

        [
            KeyboardButton("ℹ️ About"),
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

    if user_id not in user_languages:

        await update.message.reply_text(

            "✨ Welcome! 🤖\n\n"
            "I'm your smart all-in-one AI assistant.\n\n"

            "💬 AI conversations\n"
            "🧠 Study and problem solving\n"
            "✍️ Writing and translation\n"
            "🎵 Music identification\n"
            "🎬 Movie discovery\n"
            "🖼️ Photo improvement\n"
            "🔗 Link analysis\n"
            "💻 Programming help\n"
            "💡 Creative ideas\n\n"

            "🌍 Please choose your language to continue:",

            reply_markup=language_keyboard()
        )

        return

    await send_welcome(
        update,
        context
    )


# ═══════════════════════════════════════
# 🌍 خوشامدگویی بر اساس زبان
# ═══════════════════════════════════════

async def send_welcome(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id
    language = user_languages.get(
        user_id,
        "English"
    )

    welcome_text = {

        "English":
            "✨ Welcome to your Smart AI Assistant! 🤖\n\n"
            "💬 Chat with AI\n"
            "🧠 Solve problems and learn\n"
            "✍️ Write, rewrite and translate\n"
            "🎵 Find songs and music\n"
            "🎬 Discover movies and series\n"
            "🖼️ Improve and edit photos\n"
            "🔗 Analyze links\n"
            "💻 Programming assistance\n"
            "💡 Creative ideas\n\n"
            "🚀 Choose an option from the menu below.",

        "Persian":
            "✨ به دستیار هوشمند همه‌کاره خوش اومدی! 🤖\n\n"
            "💬 گفت‌وگو با هوش مصنوعی\n"
            "🧠 حل مسئله و کمک درسی\n"
            "✍️ نوشتن، بازنویسی و ترجمه\n"
            "🎵 پیدا کردن آهنگ و موسیقی\n"
            "🎬 پیدا کردن فیلم و سریال\n"
            "🖼️ بهبود و ویرایش عکس\n"
            "🔗 تحلیل لینک‌ها\n"
            "💻 کمک در برنامه‌نویسی\n"
            "💡 ایده‌پردازی و خلاقیت\n\n"
            "🚀 از منوی پایین شروع کن.",

    }

    text = welcome_text.get(
        language,
        welcome_text["English"]
    )

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🤖 ورود به AI
# ═══════════════════════════════════════

async def start_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    ai_mode.add(user_id)

    await update.message.reply_text(

        "🤖 AI Assistant\n\n"
        "✨ I'm ready!\n\n"
        "Send me any question or request.\n"
        "You can ask about almost anything.\n\n"
        "💡 Your conversation will be remembered temporarily.",

        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🧠 اتصال به Groq
# ═══════════════════════════════════════

async def ask_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id
    text = update.message.text

    if not text:
        return

    language = user_languages.get(
        user_id,
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
                "You are a professional all-purpose AI assistant. "
                f"The user's selected language is {language}. "
                "Always answer in the user's selected language. "
                "Be helpful, accurate, clear and concise. "
                "Do not claim to have abilities or tools that you do not actually have."
            )
        }

    ]

    messages.extend(
        list(ai_memory[user_id])
    )

    try:

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=messages,

            temperature=0.7,

            max_tokens=2048

        )

        answer = response.choices[0].message.content

        if not answer:

            answer = "Sorry, I couldn't generate a response."

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

        logging.exception(
            "Groq Error"
        )

        await update.message.reply_text(

            "❌ AI service error.\n\n"
            "Please try again in a few moments.",

            reply_markup=main_keyboard()
        )


# ═══════════════════════════════════════
# 🧰 ابزارها
# ═══════════════════════════════════════

async def smart_tools(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🧠 Smart Tools\n\n"

        "🎵 Music identification\n"
        "🎬 Movie discovery\n"
        "🖼️ Photo improvement\n"
        "🔗 Link analysis\n"
        "✍️ Text processing\n"
        "💻 Programming assistant\n"
        "📚 Learning assistant\n\n"

        "🚀 More tools are coming soon.",

        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🎵 آهنگ
# ═══════════════════════════════════════

async def music_finder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🎵 Music Finder\n\n"
        "Send me the song name, artist name, "
        "lyrics or any information you remember.\n\n"
        "🔜 Automatic music recognition from audio "
        "and video can be added with a music recognition API.",

        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🎬 فیلم
# ═══════════════════════════════════════

async def movie_finder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🎬 Movie Finder\n\n"
        "Tell me anything you remember about the movie:\n\n"
        "🎭 Actors\n"
        "📖 Story\n"
        "📅 Approximate year\n"
        "🎞️ A scene\n\n"
        "I'll help you identify it.",

        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🖼️ عکس
# ═══════════════════════════════════════

async def improve_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🖼️ Photo Improvement\n\n"
        "Send your photo and tell me what you want:\n\n"
        "✨ Improve quality\n"
        "🧹 Remove background\n"
        "🎨 Change style\n"
        "💡 Improve lighting\n"
        "🔍 Enhance details\n\n"
        "🔜 Real image editing requires an image processing service.",

        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🔗 لینک
# ═══════════════════════════════════════

async def analyze_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🔗 Analyze Link\n\n"
        "Send me a link and tell me what you want to know about it.\n\n"
        "📱 Social media links\n"
        "🎵 Music information\n"
        "🎬 Video content\n"
        "📝 Page summaries\n\n"
        "Some links may require an external API or web access.",

        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 👤 پروفایل
# ═══════════════════════════════════════

async def profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    user_id = user.id

    language = user_languages.get(
        user_id,
        "English"
    )

    username = (
        f"@{user.username}"
        if user.username
        else "Not set"
    )

    await update.message.reply_text(

        "╭──────────────╮\n"
        "      👤 MY PROFILE\n"
        "╰──────────────╯\n\n"

        f"✨ Name: {user.first_name or 'Unknown'}\n"
        f"🔗 Username: {username}\n"
        f"🌍 Language: {language}\n"
        f"🆔 ID: {user_id}\n\n"

        "🤖 AI Assistant User\n"
        "🧠 Smart tools enabled\n"
        "💬 AI memory active\n\n"

        "━━━━━━━━━━━━━━\n"
        "⚡ Your personal AI assistant",

        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🌍 تغییر زبان
# ═══════════════════════════════════════

async def change_language(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🌍 Choose your new language:",

        reply_markup=language_keyboard()
    )


# ═══════════════════════════════════════
# ℹ️ درباره
# ═══════════════════════════════════════

async def about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "✨ About Smart AI Assistant ✨\n\n"
        "🤖 An all-in-one AI assistant.\n\n"
        "💬 AI Chat\n"
        "🧠 Smart Tools\n"
        "🎵 Music\n"
        "🎬 Movies\n"
        "🖼️ Images\n"
        "🔗 Links\n"
        "💻 Programming\n"
        "📚 Education\n\n"
        "🚀 More features will be added over time.",

        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🔄 ریست
# ═══════════════════════════════════════

async def restart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    ai_mode.discard(user_id)

    ai_memory[user_id].clear()

    await start(
        update,
        context
    )


# ═══════════════════════════════════════
# 📨 پردازش پیام
# ═══════════════════════════════════════

async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    user_id = update.effective_user.id


    # زبان
    if text in LANGUAGES:

        user_languages[user_id] = LANGUAGES[text]

        await update.message.reply_text(

            "✅ Language selected successfully! 🌍\n\n"
            "🤖 Your AI assistant is ready.",

            reply_markup=main_keyboard()
        )

        await send_welcome(
            update,
            context
        )

        return


    # منو
    if text == "🤖 AI Chat":
        await start_ai(update, context)
        return


    if text == "🧠 Smart Tools":
        await smart_tools(update, context)
        return


    if text == "🎵 Music Finder":
        await music_finder(update, context)
        return


    if text == "🎬 Movie Finder":
        await movie_finder(update, context)
        return


    if text == "🖼️ Improve Photo":
        await improve_photo(update, context)
        return


    if text == "🔗 Analyze Link":
        await analyze_link(update, context)
        return


    if text == "👤 My Profile":
        await profile(update, context)
        return


    if text == "🌍 Change Language":
        await change_language(update, context)
        return


    if text == "ℹ️ About":
        await about(update, context)
        return


    if text == "🔄 Restart":
        await restart(update, context)
        return


    # چت AI
    if user_id in ai_mode:

        await ask_ai(
            update,
            context
        )

        return


    await update.message.reply_text(

        "👇 Please choose an option from the menu.",

        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🚀 اجرای ربات
# ═══════════════════════════════════════

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
        "🤖 Smart AI Assistant with Groq is running..."
    )

    app.run_polling()


if __name__ == "__main__":

    main()
