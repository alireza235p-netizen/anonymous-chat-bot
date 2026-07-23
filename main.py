import os
import re
import asyncio
import tempfile
import logging
from collections import defaultdict, deque

import requests

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from telegram.constants import ChatAction

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from groq import Groq


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AUDD_API_TOKEN = os.getenv("AUDD_API_TOKEN") or os.getenv("AUDD_API_KEY")
HF_TOKEN = (
    os.getenv("HF_TOKEN")
    or os.getenv("HUGGINGFACE_TOKEN")
    or os.getenv("HF_API_TOKEN")
)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

log = logging.getLogger("NEXORA")


# =========================================================
# MEMORY
# =========================================================

memory = defaultdict(lambda: deque(maxlen=20))

ai_mode = set()
private_mode = set()
waiting_movie = set()
waiting_music = set()
waiting_photo = set()

selected_language = {}


# =========================================================
# LANGUAGES
# =========================================================

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


# =========================================================
# TEXTS
# =========================================================

TEXTS = {
    "English": {
        "ai": "🤖 AI Chat",
        "tools": "🧠 Smart Tools",
        "music": "🎵 Music Finder",
        "movie": "🎬 Movie & Series Finder",
        "photo": "🖼️ Photo Tools",
        "link": "🔗 Link Tools",
        "profile": "👤 My Profile",
        "game": "🎲 Dice Rush",
        "league": "🏆 Weekly League",
        "private": "🔒 Private Chat",
        "language": "🌍 Change Language",
        "settings": "⚙️ Settings",
        "about": "ℹ️ About",
        "restart": "🔄 Restart",
    },

    "Persian": {
        "ai": "🤖 گفت‌وگوی هوشمند",
        "tools": "🧠 ابزارهای هوشمند",
        "music": "🎵 پیدا کردن آهنگ",
        "movie": "🎬 پیدا کردن فیلم و سریال",
        "photo": "🖼️ ابزار عکس",
        "link": "🔗 ابزار لینک",
        "profile": "👤 پروفایل من",
        "game": "🎲 دایس راش",
        "league": "🏆 لیگ هفتگی",
        "private": "🔒 چت خصوصی",
        "language": "🌍 تغییر زبان",
        "settings": "⚙️ تنظیمات",
        "about": "ℹ️ درباره ربات",
        "restart": "🔄 شروع دوباره",
    },
}


def t(user_id, key):
    lang = selected_language.get(user_id, "English")

    return TEXTS.get(
        lang,
        TEXTS["English"]
    ).get(
        key,
        key
    )


# =========================================================
# KEYBOARDS
# =========================================================

def language_keyboard():

    return ReplyKeyboardMarkup(
        [
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
        ],
        resize_keyboard=True,
    )


def main_keyboard(user_id):

    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(t(user_id, "ai")),
                KeyboardButton(t(user_id, "tools")),
            ],
            [
                KeyboardButton(t(user_id, "music")),
                KeyboardButton(t(user_id, "movie")),
            ],
            [
                KeyboardButton(t(user_id, "photo")),
                KeyboardButton(t(user_id, "link")),
            ],
            [
                KeyboardButton(t(user_id, "profile")),
                KeyboardButton(t(user_id, "game")),
            ],
            [
                KeyboardButton(t(user_id, "league")),
                KeyboardButton(t(user_id, "private")),
            ],
            [
                KeyboardButton(t(user_id, "language")),
                KeyboardButton(t(user_id, "settings")),
            ],
            [
                KeyboardButton(t(user_id, "about")),
                KeyboardButton(t(user_id, "restart")),
            ],
        ],
        resize_keyboard=True,
    )


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in selected_language:

        await update.message.reply_text(
            "✨ Welcome to NEXORA! 🤖🔥\n\n"
            "🌍 Please choose your language:",
            reply_markup=language_keyboard(),
        )

        return

    await welcome(update)


# =========================================================
# WELCOME
# =========================================================

async def welcome(update: Update):

    user_id = update.effective_user.id

    lang = selected_language.get(
        user_id,
        "English"
    )

    if lang == "Persian":

        text = (
            "✨ سلام رفیق! 🤖🔥\n\n"
            "به NEXORA خوش اومدی!\n\n"
            "🤖 هوش مصنوعی\n"
            "🎬 فیلم و سریال\n"
            "🎵 تشخیص آهنگ\n"
            "🖼️ افزایش کیفیت عکس\n"
            "🎲 بازی تاس\n"
            "🏆 لیگ هفتگی\n"
            "🧠 ابزارهای هوشمند\n"
            "🔒 چت خصوصی\n\n"
            "👇 از منوی پایین شروع کن."
        )

    else:

        text = (
            "✨ Welcome to NEXORA! 🤖🔥\n\n"
            "Your smart AI assistant.\n\n"
            "🤖 AI Chat\n"
            "🎬 Movies & Series\n"
            "🎵 Music Recognition\n"
            "🖼️ Image Enhancement\n"
            "🎲 Dice Rush\n"
            "🏆 Weekly League\n"
            "🧠 Smart Tools\n"
            "🔒 Private Chat\n\n"
            "👇 Choose an option."
        )

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard(user_id),
    )


# =========================================================
# AI
# =========================================================

async def start_ai(update, context):

    user_id = update.effective_user.id

    ai_mode.add(user_id)

    await update.message.reply_text(
        "🤖 AI MODE ACTIVATED!\n\n"
        "هرچی می‌خوای بپرس 😂🔥",
        reply_markup=main_keyboard(user_id),
    )


def ai_system_prompt(user_id):

    lang = selected_language.get(
        user_id,
        "English"
    )

    return f"""
You are NEXORA, a smart Telegram AI assistant.

The user's language is:
{lang}

Always answer in the user's language.

Personality:
- Fluent
- Fast
- Confident
- Funny
- Slightly cheeky
- Informal
- Clever
- Use emojis naturally

If the user insults you,
give a short playful comeback,
then continue helping.

Do not over-explain simple questions.

You can help with:
Programming
Education
Science
Technology
Writing
Translation
Movies
Series
Music
Creative ideas
Everyday questions
"""


async def ask_ai(update, context):

    user_id = update.effective_user.id

    text = update.message.text

    if not client:

        await update.message.reply_text(
            "❌ GROQ_API_KEY تنظیم نشده.",
            reply_markup=main_keyboard(user_id),
        )

        return

    memory[user_id].append(
        {
            "role": "user",
            "content": text,
        }
    )

    messages = [
        {
            "role": "system",
            "content": ai_system_prompt(user_id),
        }
    ]

    messages.extend(
        list(memory[user_id])
    )

    try:

        await update.message.chat.send_action(
            ChatAction.TYPING
        )

        result = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.85,
            max_tokens=1600,
        )

        answer = (
            result.choices[0].message.content
            or
            "🤖 مغزم رفت مرخصی 😂"
        )

        memory[user_id].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        await update.message.reply_text(
            answer,
            reply_markup=main_keyboard(user_id),
        )

    except Exception:

        log.exception("AI ERROR")

        await update.message.reply_text(
            "❌ سرویس AI فعلاً مشکل داره.",
            reply_markup=main_keyboard(user_id),
        )


# =========================================================
# MUSIC
# =========================================================

async def music(update, context):

    user_id = update.effective_user.id

    waiting_music.add(user_id)

    await update.message.reply_text(
        "🎵 اسم آهنگ یا خواننده رو بفرست.\n\n"
        "یا فایل صوتی / ویس / ویدئو بفرست "
        "تا با AUDD بررسیش کنم.",
        reply_markup=main_keyboard(user_id),
    )


async def recognize_music(update, context):

    if not AUDD_API_TOKEN:

        await update.message.reply_text(
            "❌ AUDD API تنظیم نشده."
        )

        return

    message = update.message

    file_id = None

    if message.audio:
        file_id = message.audio.file_id

    elif message.voice:
        file_id = message.voice.file_id

    elif message.video:
        file_id = message.video.file_id

    if not file_id:
        return

    temp_path = None

    try:

        telegram_file = await context.bot.get_file(
            file_id
        )

        with tempfile.NamedTemporaryFile(
            suffix=".audio",
            delete=False,
        ) as temp:

            temp_path = temp.name

        await telegram_file.download_to_drive(
            temp_path
        )

        with open(
            temp_path,
            "rb",
        ) as audio_file:

            response = requests.post(
                "https://api.audd.io/",
                data={
                    "api_token": AUDD_API_TOKEN,
                    "return": "apple_music,spotify",
                },
                files={
                    "file": audio_file
                },
                timeout=60,
            )

        data = response.json()

        result = data.get("result")

        if not result:

            await message.reply_text(
                "❌ نتونستم آهنگ رو تشخیص بدم 😕"
            )

            return

        title = result.get(
            "title",
            "Unknown"
        )

        artist = result.get(
            "artist",
            "Unknown"
        )

        album = result.get(
            "album",
            "Unknown"
        )

        release_date = result.get(
            "release_date",
            "Unknown"
        )

        text = (
            f"🎵 آهنگ پیدا شد!\n\n"
            f"🎼 Title:\n{title}\n\n"
            f"👤 Artist:\n{artist}\n\n"
            f"💿 Album:\n{album}\n\n"
            f"📅 Release:\n{release_date}"
        )

        await message.reply_text(
            text,
            reply_markup=main_keyboard(
                message.chat.id
            ),
        )

    except Exception:

        log.exception(
            "AUDD ERROR"
        )

        await message.reply_text(
            "❌ خطا هنگام تشخیص آهنگ."
        )

    finally:

        if temp_path and os.path.exists(temp_path):

            os.unlink(temp_path)


# =========================================================
# MOVIE
# =========================================================

async def movie(update, context):

    user_id = update.effective_user.id

    waiting_movie.add(user_id)

    await update.message.reply_text(
        "🎬 اسم فیلم یا سریال رو بفرست.\n\n"
        "فارسی یا انگلیسی فرقی نداره.",
        reply_markup=main_keyboard(user_id),
    )


async def search_movie(update, context):

    user_id = update.effective_user.id

    query = update.message.text.strip()

    waiting_movie.discard(user_id)

    try:

        response = requests.get(
            "https://api.tvmaze.com/search/shows",
            params={
                "q": query
            },
            timeout=10,
        )

        results = response.json()

        if not results:

            await update.message.reply_text(
                "❌ چیزی پیدا نشد.",
                reply_markup=main_keyboard(user_id),
            )

            return

        show = results[0]["show"]

        name = show.get(
            "name",
            "Unknown"
        )

        rating = (
            show.get("rating") or {}
        ).get(
            "average"
        ) or "N/A"

        genres = ", ".join(
            show.get("genres") or []
        ) or "N/A"

        language = (
            show.get("language")
            or
            "N/A"
        )

        summary = re.sub(
            r"<[^>]+>",
            "",
            show.get("summary")
            or
            "No summary.",
        )

        image = (
            show.get("image") or {}
        ).get(
            "original"
        )

        result_text = (
            f"🎬 {name}\n\n"
            f"⭐ Rating: {rating}\n\n"
            f"🌍 Language: {language}\n\n"
            f"🎭 Genres: {genres}\n\n"
            f"📝 Summary:\n{summary}"
        )

        if image:

            await update.message.reply_photo(
                photo=image,
                caption=result_text[:1024],
                reply_markup=main_keyboard(user_id),
            )

        else:

            await update.message.reply_text(
                result_text,
                reply_markup=main_keyboard(user_id),
            )

    except Exception:

        log.exception(
            "MOVIE ERROR"
        )

        await update.message.reply_text(
            "❌ خطا در جستجوی فیلم.",
            reply_markup=main_keyboard(user_id),
        )


# =========================================================
# PHOTO
# =========================================================

async def photo(update, context):

    user_id = update.effective_user.id

    waiting_photo.add(user_id)

    await update.message.reply_text(
        "🖼️ عکس رو بفرست.\n\n"
        "✨ کیفیت تصویر رو افزایش می‌دم.",
        reply_markup=main_keyboard(user_id),
    )


async def enhance_photo(update, context):

    if not HF_TOKEN:

        await update.message.reply_text(
            "❌ HF_TOKEN تنظیم نشده."
        )

        return

    user_id = update.effective_user.id

    input_path = None
    output_path = None

    try:

        photo_file = update.message.photo[-1]

        telegram_file = await context.bot.get_file(
            photo_file.file_id
        )

        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
            delete=False,
        ) as temp:

            input_path = temp.name

        await telegram_file.download_to_drive(
            input_path
        )

        with open(
            input_path,
            "rb",
        ) as image_file:

            image_bytes = image_file.read()

        model_url = (
            "https://api-inference.huggingface.co/models/"
            "caidas/swin2SR-classical-sr-x2-64"
        )

        response = requests.post(
            model_url,
            headers={
                "Authorization":
                f"Bearer {HF_TOKEN}"
            },
            data=image_bytes,
            timeout=120,
        )

        if response.status_code != 200:

            await update.message.reply_text(
                "❌ سرویس افزایش کیفیت عکس "
                "فعلاً پاسخ نداد."
            )

            return

        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        ) as output:

            output_path = output.name

            output.write(
                response.content
            )

        with open(
            output_path,
            "rb",
        ) as enhanced:

            await update.message.reply_photo(
                photo=enhanced,
                caption="✨ کیفیت عکس افزایش پیدا کرد.",
                reply_markup=main_keyboard(user_id),
            )

    except Exception:

        log.exception(
            "IMAGE ERROR"
        )

        await update.message.reply_text(
            "❌ خطا هنگام افزایش کیفیت عکس."
        )

    finally:

        if input_path and os.path.exists(input_path):
            os.unlink(input_path)

        if output_path and os.path.exists(output_path):
            os.unlink(output_path)


# =========================================================
# DICE
# =========================================================

async def dice_game(update, context):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎲 پرتاب تاس",
                    callback_data="roll_dice",
                )
            ]
        ]
    )

    await update.message.reply_text(
        "🎲 DICE RUSH\n\n"
        "روی دکمه بزن و تاس رو بنداز!\n\n"
        "🎯 اگر ۶ بیاد امتیاز ویژه می‌گیری.",
        reply_markup=keyboard,
    )


async def roll_dice(update, context):

    query = update.callback_query

    await query.answer()

    try:

        dice = await query.message.chat.send_dice(
            emoji="🎲"
        )

        value = dice.dice.value

        if value == 6:

            text = (
                "🎉 شیششششش!\n\n"
                "⭐ +10 امتیاز\n"
                "🔥 دمت گرم!"
            )

        else:

            text = (
                f"🎲 عدد {value} اومد!\n\n"
                "⭐ +1 امتیاز"
            )

        await query.message.reply_text(
            text
        )

    except Exception:

        await query.message.reply_text(
            "❌ خطا در پرتاب تاس."
        )


# =========================================================
# OTHER MENUS
# =========================================================

async def league(update, context):

    await update.message.reply_text(
        "🏆 WEEKLY LEAGUE\n\n"
        "🥇 رتبه اول\n"
        "🥈 رتبه دوم\n"
        "🥉 رتبه سوم\n\n"
        "سیستم لیگ هفتگی آماده است."
    )


async def profile(update, context):

    user = update.effective_user

    user_id = user.id

    await update.message.reply_text(
        f"👤 PROFILE\n\n"
        f"✨ Name: {user.first_name}\n"
        f"🔗 Username: @{user.username or 'N/A'}\n"
        f"🆔 ID: {user_id}\n"
        f"🌍 Language: {selected_language.get(user_id, 'English')}\n"
        f"🤖 AI: {'ON' if user_id in ai_mode else 'OFF'}\n"
        f"🔒 Private Mode: {'ON' if user_id in private_mode else 'OFF'}",
        reply_markup=main_keyboard(user_id),
    )


async def private_chat(update, context):

    user_id = update.effective_user.id

    if user_id in private_mode:

        private_mode.discard(user_id)

        await update.message.reply_text(
            "🔓 Private Mode خاموش شد.",
            reply_markup=main_keyboard(user_id),
        )

        return

    private_mode.add(user_id)

    memory[user_id].clear()

    await update.message.reply_text(
        "🔒 Private Mode فعال شد.\n\n"
        "🧹 حافظه مکالمه پاک شد.\n\n"
        "⚠️ این رمزگذاری End-to-End نیست.",
        reply_markup=main_keyboard(user_id),
    )


async def smart_tools(update, context):

    user_id = update.effective_user.id

    await update.message.reply_text(
        "🧠 SMART TOOLS\n\n"
        "📝 خلاصه‌سازی\n"
        "🌍 ترجمه\n"
        "💻 برنامه‌نویسی\n"
        "📚 کمک درسی\n"
        "🧮 حل مسئله\n"
        "💡 ایده‌پردازی\n"
        "✍️ نوشتن\n\n"
        "🤖 وارد AI Chat شو.",
        reply_markup=main_keyboard(user_id),
    )


async def link(update, context):

    user_id = update.effective_user.id

    await update.message.reply_text(
        "🔗 LINK TOOLS\n\n"
        "لینک بفرست و از AI بخواه:\n\n"
        "📝 خلاصه کن\n"
        "🔎 تحلیل کن\n"
        "🌍 ترجمه کن\n"
        "📚 توضیح بده",
        reply_markup=main_keyboard(user_id),
    )


async def settings(update, context):

    user_id = update.effective_user.id

    await update.message.reply_text(
        "⚙️ Settings",
        reply_markup=main_keyboard(user_id),
    )


async def about(update, context):

    user_id = update.effective_user.id

    await update.message.reply_text(
        "✨ NEXORA AI ✨\n\n"
        "🤖 Groq AI\n"
        "🎵 AUDD Music Recognition\n"
        "🖼️ Hugging Face Image Enhancement\n"
        "🎬 TVmaze Search\n"
        "🎲 Dice Rush\n"
        "🏆 Weekly League\n"
        "🌍 Multi-language\n"
        "🔒 Private Mode\n"
        "🧠 AI Memory",
        reply_markup=main_keyboard(user_id),
    )


async def change_language(update, context):

    await update.message.reply_text(
        "🌍 زبان رو انتخاب کن:",
        reply_markup=language_keyboard(),
    )


async def restart(update, context):

    user_id = update.effective_user.id

    ai_mode.discard(user_id)
    private_mode.discard(user_id)
    waiting_movie.discard(user_id)
    waiting_music.discard(user_id)
    waiting_photo.discard(user_id)

    memory[user_id].clear()

    await welcome(update)


# =========================================================
# MUSIC TEXT SEARCH
# =========================================================

async def search_music_text(update, context):

    user_id = update.effective_user.id

    query = update.message.text

    waiting_music.discard(user_id)

    await update.message.reply_text(
        f"🎵 Music Search\n\n"
        f"🔎 {query}\n\n"
        f"برای تشخیص از روی فایل صوتی، "
        f"فایل رو همین‌جا بفرست.",
        reply_markup=main_keyboard(user_id),
    )


# =========================================================
# TEXT HANDLER
# =========================================================

async def handle_text(update, context):

    user_id = update.effective_user.id

    text = update.message.text.strip()

    # LANGUAGE
    if text in LANGUAGES:

        selected_language[user_id] = LANGUAGES[text]

        memory[user_id].clear()

        await welcome(update)

        return

    # MOVIE SEARCH
    if user_id in waiting_movie:

        await search_movie(
            update,
            context
        )

        return

    # MUSIC SEARCH
    if user_id in waiting_music:

        await search_music_text(
            update,
            context
        )

        return

    # AI BUTTON
    if text == t(user_id, "ai"):

        await start_ai(
            update,
            context
        )

        return

    # TOOLS
    if text == t(user_id, "tools"):

        await smart_tools(
            update,
            context
        )

        return

    # MUSIC
    if text == t(user_id, "music"):

        await music(
            update,
            context
        )

        return

    # MOVIE
    if text == t(user_id, "movie"):

        await movie(
            update,
            context
        )

        return

    # PHOTO
    if text == t(user_id, "photo"):

        await photo(
            update,
            context
        )

        return

    # LINK
    if text == t(user_id, "link"):

        await link(
            update,
            context
        )

        return

    # PROFILE
    if text == t(user_id, "profile"):

        await profile(
            update,
            context
        )

        return

    # GAME
    if text == t(user_id, "game"):

        await dice_game(
            update,
            context
        )

        return

    # LEAGUE
    if text == t(user_id, "league"):

        await league(
            update,
            context
        )

        return

    # PRIVATE
    if text == t(user_id, "private"):

        await private_chat(
            update,
            context
        )

        return

    # LANGUAGE
    if text == t(user_id, "language"):

        await change_language(
            update,
            context
        )

        return

    # SETTINGS
    if text == t(user_id, "settings"):

        await settings(
            update,
            context
        )

        return

    # ABOUT
    if text == t(user_id, "about"):

        await about(
            update,
            context
        )

        return

    # RESTART
    if text == t(user_id, "restart"):

        await restart(
            update,
            context
        )

        return

    # AI MODE
    if user_id in ai_mode:

        await ask_ai(
            update,
            context
        )

        return

    await update.message.reply_text(
        "👇 از منوی پایین انتخاب کن.",
        reply_markup=main_keyboard(user_id),
    )


# =========================================================
# MEDIA HANDLER
# =========================================================

async def handle_media(update, context):

    if (
        update.message.audio
        or update.message.voice
        or update.message.video
    ):

        await recognize_music(
            update,
            context
        )

        return

    if update.message.photo:

        await enhance_photo(
            update,
            context
        )

        return


# =========================================================
# MAIN
# =========================================================

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
        CallbackQueryHandler(
            roll_dice,
            pattern="^roll_dice$"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO
            | filters.AUDIO
            | filters.VOICE
            | filters.VIDEO,
            handle_media
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
        "🤖 NEXORA is running..."
    )

    app.run_polling(
        drop_pending_updates=True
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
