import os
import logging
import random
import re
import requests

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


# =========================================================
# ⚙️ CONFIG
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AUDD_API_TOKEN = os.getenv("AUDD_API_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing")

if not AUDD_API_TOKEN:
    logging.warning("AUDD_API_TOKEN is missing. Music recognition will be disabled.")


client = Groq(
    api_key=GROQ_API_KEY
)


# =========================================================
# 🧠 MEMORY
# =========================================================

memory = defaultdict(
    lambda: deque(maxlen=16)
)

selected_language = {}

ai_mode = set()

private_mode = set()


# =========================================================
# 🌍 LANGUAGES
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

        resize_keyboard=True

    )


# =========================================================
# 🎨 TRANSLATIONS
# =========================================================

TEXTS = {

    "English": {

        "ai": "🤖 AI Chat",
        "tools": "🧠 Smart Tools",
        "music": "🎵 Music Finder",
        "movie": "🎬 Series Finder",
        "photo": "🖼️ Photo Tools",
        "link": "🔗 Link Tools",
        "profile": "👤 My Profile",
        "game": "🎲 Truth or Dare",
        "private": "🔒 Private Chat",
        "language": "🌍 Change Language",
        "settings": "⚙️ Settings",
        "about": "ℹ️ About",
        "restart": "🔄 Restart",

    },


    "Persian": {

        "ai": "🤖 گفت‌وگو با AI",
        "tools": "🧠 ابزارهای هوشمند",
        "music": "🎵 پیدا کردن آهنگ",
        "movie": "🎬 پیدا کردن سریال",
        "photo": "🖼️ ابزار عکس",
        "link": "🔗 ابزار لینک",
        "profile": "👤 پروفایل من",
        "game": "🎲 جرئت یا حقیقت",
        "private": "🔒 چت خصوصی",
        "language": "🌍 تغییر زبان",
        "settings": "⚙️ تنظیمات",
        "about": "ℹ️ درباره ربات",
        "restart": "🔄 شروع دوباره",

    },

}


def t(user_id, key):

    lang = selected_language.get(
        user_id,
        "English"
    )

    if lang in TEXTS:

        return TEXTS[lang].get(
            key,
            TEXTS["English"].get(key, key)
        )

    return TEXTS["English"].get(
        key,
        key
    )


# =========================================================
# 🎨 MAIN KEYBOARD
# =========================================================

def main_keyboard(user_id):

    return ReplyKeyboardMarkup(

        [

            [
                KeyboardButton(
                    t(user_id, "ai")
                ),

                KeyboardButton(
                    t(user_id, "tools")
                ),

            ],

            [
                KeyboardButton(
                    t(user_id, "music")
                ),

                KeyboardButton(
                    t(user_id, "movie")
                ),

            ],

            [
                KeyboardButton(
                    t(user_id, "photo")
                ),

                KeyboardButton(
                    t(user_id, "link")
                ),

            ],

            [
                KeyboardButton(
                    t(user_id, "profile")
                ),

                KeyboardButton(
                    t(user_id, "game")
                ),

            ],

            [
                KeyboardButton(
                    t(user_id, "private")
                ),

                KeyboardButton(
                    t(user_id, "language")
                ),

            ],

            [
                KeyboardButton(
                    t(user_id, "settings")
                ),

                KeyboardButton(
                    t(user_id, "about")
                ),

            ],

            [
                KeyboardButton(
                    t(user_id, "restart")
                ),

            ],

        ],

        resize_keyboard=True

    )


# =========================================================
# 👋 START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    user_id = user.id

    if user_id not in selected_language:

        await update.message.reply_text(

            "✨ Welcome! 🤖🔥\n\n"

            "I'm your all-in-one AI assistant.\n\n"

            "💬 AI Chat\n"
            "🧠 Smart Tools\n"
            "🎵 Music Finder\n"
            "📺 Series Finder\n"
            "🖼️ Image Tools\n"
            "🔗 Link Tools\n"
            "🎲 Truth or Dare\n"
            "🔒 Private Chat\n"
            "💻 Programming\n"
            "📚 Education\n\n"

            "🌍 Please choose your language:",

            reply_markup=language_keyboard()

        )

        return


    await welcome(
        update,
        context
    )


# =========================================================
# 🌍 WELCOME
# =========================================================

async def welcome(
    update,
    context
):

    user_id = update.effective_user.id

    lang = selected_language.get(
        user_id,
        "English"
    )


    if lang == "Persian":

        text = (

            "✨ سلام رفیق! 🤖🔥\n\n"

            "به دستیار هوشمند همه‌کاره خوش اومدی!\n\n"

            "💬 گفت‌وگو با هوش مصنوعی\n"
            "🧠 حل سؤال و کمک درسی\n"
            "✍️ نوشتن و ترجمه\n"
            "🎵 پیدا کردن آهنگ از فایل صوتی و Voice\n"
            "📺 پیدا کردن سریال و اطلاعات کاملش\n"
            "🖼️ ابزارهای هوشمند عکس\n"
            "🔗 بررسی لینک‌ها\n"
            "🎲 بازی جرئت یا حقیقت\n"
            "🔒 چت خصوصی\n"
            "💻 برنامه‌نویسی\n"
            "😂 و البته کلی طنز و شیطنت!\n\n"

            "🚀 از منوی پایین شروع کن."

        )

    else:

        text = (

            "✨ Welcome! 🤖🔥\n\n"

            "Your all-in-one AI assistant is ready!\n\n"

            "💬 AI Chat\n"
            "🧠 Smart Tools\n"
            "✍️ Writing & Translation\n"
            "🎵 Music Finder\n"
            "📺 Series Finder\n"
            "🖼️ Image Tools\n"
            "🔗 Link Tools\n"
            "🎲 Truth or Dare\n"
            "🔒 Private Chat\n"
            "💻 Programming\n"
            "😂 And plenty of humor!\n\n"

            "🚀 Choose an option below."

        )


    await update.message.reply_text(

        text,

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# 🤖 AI MODE
# =========================================================

async def start_ai(
    update,
    context
):

    user_id = update.effective_user.id

    ai_mode.add(
        user_id
    )


    await update.message.reply_text(

        "🤖 AI MODE ACTIVATED\n\n"

        "Ask me anything.\n\n"

        "🧠 Study\n"
        "💻 Programming\n"
        "✍️ Writing\n"
        "🎬 Movies & Series\n"
        "🎵 Music\n"
        "💡 Ideas\n\n"

        "😎 I'm ready.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# 🧠 AI
# =========================================================

async def ask_ai(
    update,
    context
):

    user_id = update.effective_user.id

    user_text = update.message.text

    lang = selected_language.get(
        user_id,
        "English"
    )


    memory[user_id].append(

        {
            "role": "user",
            "content": user_text
        }

    )


    system_prompt = f"""

You are a powerful all-purpose AI assistant.

The user's selected language is:
{lang}

Always answer in the selected language.

Your personality:

- Intelligent
- Funny
- Confident
- Energetic
- Friendly
- Uses emojis naturally
- Can use clever sarcasm
- Can make playful jokes
- Can respond to insults with witty humor

Never threaten the user.
Never use hateful content.
Always try to be useful.

Help with:

Study
Programming
Writing
Translation
Science
Technology
Movies
Series
Music
Creative ideas
Everyday questions

If the user insults you, respond with a short witty comeback and continue helping.
"""


    messages = [

        {
            "role": "system",
            "content": system_prompt
        }

    ]


    messages.extend(
        list(
            memory[user_id]
        )
    )


    try:

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=messages,

            temperature=0.85,

            max_tokens=2048

        )


        answer = (

            response
            .choices[0]
            .message
            .content

        )


        if not answer:

            answer = (
                "🤖 My brain just went on coffee break. 😂"
            )


        memory[user_id].append(

            {
                "role": "assistant",
                "content": answer
            }

        )


        await update.message.reply_text(

            answer,

            reply_markup=main_keyboard(
                user_id
            )

        )


    except Exception:

        logging.exception(
            "Groq Error"
        )


        await update.message.reply_text(

            "❌ AI service error.\n\n"
            "Please try again.",

            reply_markup=main_keyboard(
                user_id
            )

        )


# =========================================================
# 👤 PROFILE
# =========================================================

async def profile(
    update,
    context
):

    user = update.effective_user

    user_id = user.id


    username = (

        f"@{user.username}"

        if user.username

        else "Not set"

    )


    await update.message.reply_text(

        f"╭──────────────╮\n"
        f"       👤 PROFILE\n"
        f"╰──────────────╯\n\n"

        f"✨ Name: {user.first_name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: {user_id}\n"
        f"🌍 Language: "
        f"{selected_language.get(user_id, 'English')}\n\n"

        f"🤖 AI Assistant User\n"
        f"🧠 AI Memory: Active\n"
        f"🎲 Games: Available\n"
        f"🔒 Private Mode: Available\n\n"

        f"⚡ Powered by Groq",

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# 🔒 PRIVATE MODE
# =========================================================

async def private_chat(
    update,
    context
):

    user_id = update.effective_user.id


    if user_id in private_mode:

        private_mode.discard(
            user_id
        )


        await update.message.reply_text(

            "🔓 Private mode disabled.",

            reply_markup=main_keyboard(
                user_id
            )

        )

        return


    private_mode.add(
        user_id
    )


    memory[user_id].clear()


    await update.message.reply_text(

        "🔒 Private Mode Enabled.\n\n"

        "🧹 AI memory cleared.\n"
        "🧠 Temporary conversation mode enabled.\n\n"

        "⚠️ This is NOT end-to-end encryption.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# 🎲 TRUTH OR DARE
# =========================================================

truth_questions = [

    "What is your biggest fear?",
    "What is your most embarrassing moment?",
    "What is your weirdest habit?",
    "What is something you never told your friends?",
    "Who knows you better than anyone?",

]


dare_questions = [

    "Send a funny voice message.",
    "Change your profile picture for 5 minutes.",
    "Write a completely random sentence.",
    "Send your funniest emoji combination.",
    "Tell a joke without laughing.",

]


async def truth_dare(
    update,
    context
):

    user_id = update.effective_user.id


    choice = random.choice(

        [
            "truth",
            "dare"
        ]

    )


    if choice == "truth":

        question = random.choice(
            truth_questions
        )


        text = (

            "🎲 TRUTH\n\n"
            f"❓ {question}\n\n"
            "👥 Send it to your friend."

        )


    else:

        question = random.choice(
            dare_questions
        )


        text = (

            "🎲 DARE\n\n"
            f"🔥 {question}\n\n"
            "👥 Send it to your friend."

        )


    await update.message.reply_text(

        text,

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# 🎵 MUSIC MENU
# =========================================================

async def music(
    update,
    context
):

    user_id = update.effective_user.id


    await update.message.reply_text(

        "🎵 Music Finder 🎶\n\n"

        "یک فایل صوتی یا Voice بفرست.\n\n"

        "🎧 من تلاش می‌کنم اسم آهنگ و خواننده رو پیدا کنم.\n\n"

        "💡 هرچی قسمت آهنگ واضح‌تر باشه، "
        "احتمال شناسایی بیشتره.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# 🎵 MUSIC RECOGNITION
# =========================================================

async def recognize_music(
    update,
    context
):

    user_id = update.effective_user.id

    temp_file = None


    if not AUDD_API_TOKEN:

        await update.message.reply_text(

            "❌ Music recognition is not configured yet.\n\n"
            "AUDD_API_TOKEN is missing.",

            reply_markup=main_keyboard(
                user_id
            )

        )

        return


    try:

        if update.message.audio:

            file_id = (
                update.message.audio.file_id
            )

            extension = ".mp3"


        elif update.message.voice:

            file_id = (
                update.message.voice.file_id
            )

            extension = ".ogg"


        else:

            return


        telegram_file = await context.bot.get_file(
            file_id
        )


        temp_file = (

            f"/tmp/music_"
            f"{user_id}_"
            f"{random.randint(1000,9999)}"
            f"{extension}"

        )


        await telegram_file.download_to_drive(
            custom_path=temp_file
        )


        await update.message.reply_text(

            "🎵 دارم آهنگ رو شناسایی می‌کنم... 🔎🎶"

        )


        with open(
            temp_file,
            "rb"
        ) as audio_file:

            response = requests.post(

                "https://api.audd.io/",

                data={

                    "api_token": AUDD_API_TOKEN,

                    "return": "spotify,apple_music"

                },

                files={

                    "file": audio_file

                },

                timeout=30

            )


        if response.status_code != 200:

            await update.message.reply_text(

                "❌ سرویس تشخیص آهنگ پاسخ مناسبی نداد.",

                reply_markup=main_keyboard(
                    user_id
                )

            )

            return


        data = response.json()


        if data.get("status") != "success":

            await update.message.reply_text(

                "❌ خطا در سرویس تشخیص آهنگ.",

                reply_markup=main_keyboard(
                    user_id
                )

            )

            return


        result = data.get(
            "result"
        )


        if not result:

            await update.message.reply_text(

                "😕 نتونستم آهنگ رو شناسایی کنم.\n\n"
                "🎵 یک قسمت واضح‌تر از آهنگ بفرست.",

                reply_markup=main_keyboard(
                    user_id
                )

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


        song_link = result.get(
            "song_link"
        )


        text = (

            "🎵 آهنگ شناسایی شد! 🎉\n\n"

            f"🎼 آهنگ: {title}\n"

            f"🎤 خواننده: {artist}\n"

            f"💿 آلبوم: {album}\n"

            f"📅 تاریخ انتشار: {release_date}\n"

        )


        if song_link:

            text += (

                f"\n🔗 لینک آهنگ:\n"
                f"{song_link}"

            )


        await update.message.reply_text(

            text,

            reply_markup=main_keyboard(
                user_id
            )

        )


    except Exception:

        logging.exception(
            "Music Recognition Error"
        )


        await update.message.reply_text(

            "❌ هنگام تشخیص آهنگ مشکلی پیش اومد.\n\n"
            "🎧 یک فایل صوتی کوتاه و واضح‌تر امتحان کن.",

            reply_markup=main_keyboard(
                user_id
            )

        )


    finally:

        if temp_file and os.path.exists(
            temp_file
        ):

            try:

                os.remove(
                    temp_file
                )

            except Exception:

                pass


# =========================================================
# 🎬 TVMAZE SERIES MENU
# =========================================================

async def movie(
    update,
    context
):

    user_id = update.effective_user.id


    context.user_data[
        "waiting_for_show"
    ] = True


    await update.message.reply_text(

        "🎬 اسم فیلم یا سریال رو بفرست.\n\n"

        "مثلاً:\n"

        "Breaking Bad\n"
        "بریکینگ بد\n"
        "Game of Thrones\n"
        "بازی تاج و تخت\n\n"

        "🔎 من تلاش می‌کنم عنوان درست رو پیدا کنم.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# 📺 SEARCH TVMAZE + GROQ TRANSLATION
# =========================================================

async def search_tvmaze(
    update,
    context
):

    user_id = update.effective_user.id

    query = update.message.text.strip()


    context.user_data[
        "waiting_for_show"
    ] = False


    try:

        # -------------------------------------------------
        # تبدیل نام فارسی به عنوان انگلیسی
        # -------------------------------------------------

        translation_response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[

                {

                    "role": "system",

                    "content": (

                        "Convert the user's movie or TV show name "
                        "into its most likely official English title. "
                        "If the input is already English, return it unchanged. "
                        "Return ONLY the title. "
                        "Do not explain."

                    )

                },

                {

                    "role": "user",

                    "content": query

                }

            ],

            temperature=0,

            max_tokens=50

        )


        search_query = (

            translation_response
            .choices[0]
            .message
            .content
            .strip()

        )


        # -------------------------------------------------
        # جستجوی TVmaze
        # -------------------------------------------------

        response = requests.get(

            "https://api.tvmaze.com/singlesearch/shows",

            params={

                "q": search_query,

                "embed": "cast"

            },

            timeout=10

        )


        # اگر پیدا نشد، خود متن کاربر را امتحان کن

        if response.status_code != 200:

            response = requests.get(

                "https://api.tvmaze.com/singlesearch/shows",

                params={

                    "q": query,

                    "embed": "cast"

                },

                timeout=10

            )


        if response.status_code != 200:

            await update.message.reply_text(

                "❌ چیزی با این اسم پیدا نکردم.\n\n"
                "اسم فیلم یا سریال رو کمی دقیق‌تر بفرست.",

                reply_markup=main_keyboard(
                    user_id
                )

            )

            return


        show = response.json()


        name = show.get(
            "name",
            "Unknown"
        )


        rating = (

            show.get(
                "rating",
                {}
            ).get(
                "average"
            )

            or "N/A"

        )


        language = (

            show.get(
                "language"
            )

            or "N/A"

        )


        premiered = (

            show.get(
                "premiered"
            )

            or "N/A"

        )


        genres = ", ".join(

            show.get(
                "genres",
                []
            )

        ) or "N/A"


        summary = show.get(

            "summary",

            "No description available."

        )


        summary = re.sub(

            "<.*?>",

            "",

            summary

        )


        official_url = (

            show.get(
                "officialSite"
            )

            or show.get(
                "url"
            )

            or "N/A"

        )


        poster = (

            show.get(
                "image",
                {}
            ).get(
                "original"
            )

        )


        cast = (

            show.get(
                "_embedded",
                {}
            ).get(
                "cast",
                []
            )

        )


        actors = []


        for item in cast[:5]:

            person = item.get(
                "person",
                {}
            )


            character = item.get(
                "character",
                {}
            )


            person_name = person.get(
                "name"
            )


            character_name = character.get(
                "name",
                "Unknown"
            )


            if person_name:

                actors.append(

                    f"{person_name} "
                    f"({character_name})"

                )


        actors_text = (

            "\n".join(
                actors
            )

            if actors

            else "N/A"

        )


        result = (

            f"🎬 {name}\n\n"

            f"⭐ Rating: {rating}\n"
            f"🌍 Language: {language}\n"
            f"📅 Premiered: {premiered}\n"
            f"🎭 Genres: {genres}\n\n"

            f"👥 Cast:\n"
            f"{actors_text}\n\n"

            f"📝 Summary:\n"
            f"{summary}\n\n"

            f"🔗 Official Page:\n"
            f"{official_url}"

        )


        if poster:

            await update.message.reply_photo(

                photo=poster,

                caption=result[:1024],

                reply_markup=main_keyboard(
                    user_id
                )

            )

        else:

            await update.message.reply_text(

                result,

                reply_markup=main_keyboard(
                    user_id
                )

            )


    except Exception:

        logging.exception(
            "TVmaze Error"
        )


        await update.message.reply_text(

            "❌ خطایی هنگام جستجوی فیلم یا سریال رخ داد.",

            reply_markup=main_keyboard(
                user_id
            )

        )


# =========================================================
# 🖼️ PHOTO
# =========================================================

async def photo(
    update,
    context
):

    user_id = update.effective_user.id


    await update.message.reply_text(

        "🖼️ Photo Tools\n\n"

        "عکس رو بفرست و بگو چه تغییری می‌خوای:\n\n"

        "✨ افزایش کیفیت\n"
        "🧹 حذف پس‌زمینه\n"
        "🎨 تغییر سبک\n"
        "💡 بهبود نور\n"
        "🔍 افزایش جزئیات\n\n"

        "⚠️ برای ویرایش واقعی تصویر باید "
        "سرویس پردازش تصویر متصل شود.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# 🔗 LINK
# =========================================================

async def link(
    update,
    context
):

    user_id = update.effective_user.id


    await update.message.reply_text(

        "🔗 Link Tools\n\n"

        "لینک موردنظرت رو بفرست.\n\n"

        "📱 شبکه‌های اجتماعی\n"
        "🎵 موسیقی\n"
        "🎬 ویدئو\n"
        "📝 خلاصه‌سازی\n\n"

        "⚠️ تحلیل کامل بعضی سایت‌ها "
        "به سرویس مخصوص نیاز دارد.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# 🧠 SMART TOOLS
# =========================================================

async def smart_tools(
    update,
    context
):

    user_id = update.effective_user.id


    await update.message.reply_text(

        "🧠 Smart Tools\n\n"

        "📝 خلاصه‌سازی متن\n"
        "🌍 ترجمه\n"
        "💻 برنامه‌نویسی\n"
        "📚 کمک درسی\n"
        "🧮 حل مسئله\n"
        "💡 ایده‌پردازی\n"
        "✍️ نوشتن متن\n\n"

        "🤖 وارد AI Chat شو و درخواستت رو بنویس.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# 🌍 CHANGE LANGUAGE
# =========================================================

async def change_language(
    update,
    context
):

    await update.message.reply_text(

        "🌍 Choose your language:",

        reply_markup=language_keyboard()

    )


# =========================================================
# ⚙️ SETTINGS
# =========================================================

async def settings(
    update,
    context
):

    user_id = update.effective_user.id


    await update.message.reply_text(

        "⚙️ Settings\n\n"

        "🌍 Change Language\n"
        "🔒 Private Mode\n"
        "🧠 AI Memory\n"
        "🔄 Restart",

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# ℹ️ ABOUT
# =========================================================

async def about(
    update,
    context
):

    user_id = update.effective_user.id


    await update.message.reply_text(

        "✨ Smart AI Assistant ✨\n\n"

        "🤖 Powered by Groq\n"
        "🌍 Multi-language\n"
        "🧠 AI Chat\n"
        "📺 TVmaze Series Search\n"
        "🎲 Truth or Dare\n"
        "🎵 AudD Music Recognition\n"
        "🖼️ Photo Tools\n"
        "🔗 Link Tools\n"
        "🔒 Private Mode\n\n"

        "🚀 More features coming soon!",

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# 🔄 RESTART
# =========================================================

async def restart(
    update,
    context
):

    user_id = update.effective_user.id


    ai_mode.discard(
        user_id
    )


    private_mode.discard(
        user_id
    )


    memory[user_id].clear()


    context.user_data.clear()


    await welcome(

        update,

        context

    )


# =========================================================
# 📨 HANDLE TEXT
# =========================================================

async def handle_text(
    update,
    context
):

    user_id = update.effective_user.id

    text = update.message.text.strip()


    # =====================================================
    # 🌍 LANGUAGE
    # =====================================================

    if text in LANGUAGES:

        selected_language[user_id] = LANGUAGES[text]

        ai_mode.discard(
            user_id
        )

        memory[user_id].clear()


        await update.message.reply_text(

            "✅ Language updated successfully! 🌍",

            reply_markup=main_keyboard(
                user_id
            )

        )


        await welcome(

            update,

            context

        )

        return


    # =====================================================
    # 🎬 TVMAZE SEARCH
    # =====================================================

    if context.user_data.get(
        "waiting_for_show"
    ):

        await search_tvmaze(
            update,
            context
        )

        return


    # =====================================================
    # 🤖 AI
    # =====================================================

    if text == t(
        user_id,
        "ai"
    ):

        await start_ai(
            update,
            context
        )

        return


    # =====================================================
    # 🧠 TOOLS
    # =====================================================

    if text == t(
        user_id,
        "tools"
    ):

        await smart_tools(
            update,
            context
        )

        return


    # =====================================================
    # 🎵 MUSIC
    # =====================================================

    if text == t(
        user_id,
        "music"
    ):

        await music(
            update,
            context
        )

        return


    # =====================================================
    # 🎬 MOVIE / SERIES
    # =====================================================

    if text == t(
        user_id,
        "movie"
    ):

        await movie(
            update,
            context
        )

        return


    # =====================================================
    # 🖼️ PHOTO
    # =====================================================

    if text == t(
        user_id,
        "photo"
    ):

        await photo(
            update,
            context
        )

        return


    # =====================================================
    # 🔗 LINK
    # =====================================================

    if text == t(
        user_id,
        "link"
    ):

        await link(
            update,
            context
        )

        return


    # =====================================================
    # 👤 PROFILE
    # =====================================================

    if text == t(
        user_id,
        "profile"
    ):

        await profile(
            update,
            context
        )

        return


    # =====================================================
    # 🎲 GAME
    # =====================================================

    if text == t(
        user_id,
        "game"
    ):

        await truth_dare(
            update,
            context
        )

        return


    # =====================================================
    # 🔒 PRIVATE
    # =====================================================

    if text == t(
        user_id,
        "private"
    ):

        await private_chat(
            update,
            context
        )

        return


    # =====================================================
    # 🌍 LANGUAGE MENU
    # =====================================================

    if text == t(
        user_id,
        "language"
    ):

        await change_language(
            update,
            context
        )

        return


    # =====================================================
    # ⚙️ SETTINGS
    # =====================================================

    if text == t(
        user_id,
        "settings"
    ):

        await settings(
            update,
            context
        )

        return


    # =====================================================
    # ℹ️ ABOUT
    # =====================================================

    if text == t(
        user_id,
        "about"
    ):

        await about(
            update,
            context
        )

        return


    # =====================================================
    # 🔄 RESTART
    # =====================================================

    if text == t(
        user_id,
        "restart"
    ):

        await restart(
            update,
            context
        )

        return


    # =====================================================
    # 🤖 AI CHAT
    # =====================================================

    if user_id in ai_mode:

        await ask_ai(
            update,
            context
        )

        return


    # =====================================================
    # DEFAULT
    # =====================================================

    await update.message.reply_text(

        "👇 Please choose an option from the menu.",

        reply_markup=main_keyboard(
            user_id
        )

    )


# =========================================================
# 🚀 MAIN
# =========================================================

def main():

    app = (

        Application

        .builder()

        .token(
            BOT_TOKEN
        )

        .build()

    )


    # /start

    app.add_handler(

        CommandHandler(

            "start",

            start

        )

    )


    # 🎵 Audio Files

    app.add_handler(

        MessageHandler(

            filters.AUDIO,

            recognize_music

        )

    )


    # 🎙️ Voice Messages

    app.add_handler(

        MessageHandler(

            filters.VOICE,

            recognize_music

        )

    )


    # 💬 Text

    app.add_handler(

        MessageHandler(

            filters.TEXT

            & ~filters.COMMAND,

            handle_text

        )

    )


    print(

        "🤖 Smart AI Assistant is running..."

    )


    app.run_polling()


# =========================================================
# ▶️ RUN
# =========================================================

if __name__ == "__main__":

    main()
