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
# 🧠 حافظه مکالمه
# ═══════════════════════════════════════

ai_memory = defaultdict(
    lambda: deque(maxlen=12)
)

ai_mode = set()


# ═══════════════════════════════════════
# 🎨 منوی حرفه‌ای
# ═══════════════════════════════════════

def main_keyboard():

    keyboard = [

        [
            KeyboardButton("🤖 گفت‌وگو با AI"),
            KeyboardButton("🧠 ابزارهای هوشمند"),
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
            KeyboardButton("ℹ️ درباره دستیار"),
            KeyboardButton("🔄 شروع دوباره"),
        ],

    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


# ═══════════════════════════════════════
# 👋 پیام خوشامدگویی
# ═══════════════════════════════════════

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    await update.message.reply_text(

        f"✨ سلام {user.first_name or 'دوست من'}! ✨\n\n"

        "🤖 به دستیار هوشمند همه‌کاره خوش اومدی!\n\n"

        "اینجا فقط یک چت‌بات معمولی نیستی؛ "
        "می‌تونی برای کلی کار مختلف ازم کمک بگیری:\n\n"

        "💬 گفت‌وگوی هوشمند و پاسخ به سؤال‌ها\n"
        "🧠 کمک در درس، تحقیق و حل مسئله\n"
        "✍️ نوشتن، بازنویسی و ترجمه متن\n"
        "🎵 پیدا کردن اسم آهنگ و اطلاعات موسیقی\n"
        "🎬 کمک برای پیدا کردن فیلم و سریال\n"
        "🖼️ کمک برای بهبود و ویرایش عکس\n"
        "🔗 بررسی و تحلیل لینک‌ها\n"
        "📱 کمک برای محتوای شبکه‌های اجتماعی\n"
        "💡 ایده‌پردازی و خلاقیت\n"
        "💻 کمک در برنامه‌نویسی و کدنویسی\n\n"

        "🚀 هدف اینه که هر چیزی لازم داری، "
        "تا جای ممکن همین‌جا انجامش بدی.\n\n"

        "👇 از منوی پایین شروع کن:",

        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🤖 ورود به چت AI
# ═══════════════════════════════════════

async def start_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    ai_mode.add(user_id)

    ai_memory[user_id].clear()

    await update.message.reply_text(

        "╭───────────────╮\n"
        "   🤖 دستیار هوشمند\n"
        "╰───────────────╯\n\n"

        "✨ آماده‌ام!\n\n"

        "هر سؤالی داری بپرس.\n"
        "می‌تونی درباره درس، برنامه‌نویسی، فیلم، موسیقی، "
        "ایده‌پردازی، متن و کلی موضوع دیگه باهام صحبت کنی.\n\n"

        "💡 فقط پیامت رو بفرست.\n\n"

        "🔙 برای خروج، دکمه «🔄 شروع دوباره» رو بزن.",

        reply_markup=main_keyboard()
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
                "تو یک دستیار هوش مصنوعی همه‌کاره و حرفه‌ای هستی. "
                "به زبان کاربر پاسخ بده. "
                "پاسخ‌ها را واضح، دقیق و کاربردی بنویس. "
                "اگر کاربر فارسی صحبت کرد فارسی جواب بده. "
                "اگر کاری نیاز به ابزار یا API خارجی داشته باشد "
                "صادقانه توضیح بده که برای انجام واقعی آن قابلیت "
                "به سرویس مربوطه نیاز است."
            )
        }

    ]


    messages.extend(
        list(ai_memory[user_id])
    )


    try:

        response = client.responses.create(

            model="gpt-4o-mini",

            input=messages

        )


        answer = response.output_text


        if not answer:

            answer = "❌ پاسخی دریافت نشد."


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


    except Exception:

        logging.exception(
            "OpenAI Error:"
        )


        await update.message.reply_text(

            "❌ مشکلی در اتصال به هوش مصنوعی پیش اومد.\n\n"
            "لطفاً چند لحظه دیگه دوباره امتحان کن.",

            reply_markup=main_keyboard()

        )


# ═══════════════════════════════════════
# 🧠 ابزارهای هوشمند
# ═══════════════════════════════════════

async def smart_tools(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🧠 ابزارهای هوشمند\n\n"

        "🎵 تشخیص و پیدا کردن آهنگ\n"
        "🎬 پیدا کردن فیلم و سریال\n"
        "🖼️ بهبود و ویرایش تصویر\n"
        "🔗 تحلیل لینک‌ها\n"
        "✍️ پردازش و بازنویسی متن\n"
        "💻 دستیار برنامه‌نویسی\n"
        "📚 دستیار آموزشی\n\n"

        "🚀 قابلیت‌های بیشتر به‌مرور به این بخش اضافه می‌شن.",

        reply_markup=main_keyboard()

    )


# ═══════════════════════════════════════
# 🎵 تشخیص آهنگ
# ═══════════════════════════════════════

async def music_finder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🎵 تشخیص آهنگ\n\n"

        "فعلاً اسم آهنگ، خواننده یا بخشی از متن آهنگ رو برام بنویس.\n\n"

        "🔜 قابلیت تشخیص خودکار آهنگ از فایل صوتی و ویدئو "
        "در مرحله بعد به ربات اضافه می‌شه.",

        reply_markup=main_keyboard()

    )


# ═══════════════════════════════════════
# 🎬 پیدا کردن فیلم
# ═══════════════════════════════════════

async def movie_finder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🎬 پیدا کردن فیلم و سریال\n\n"

        "اسم فیلم، بازیگر، داستان یا هر چیزی که از فیلم یادت میاد "
        "برام بنویس تا برای پیدا کردنش راهنماییت کنم.\n\n"

        "🔜 جستجوی مستقیم در پایگاه‌های فیلم هم "
        "در نسخه‌های بعدی اضافه می‌شه.",

        reply_markup=main_keyboard()

    )


# ═══════════════════════════════════════
# 🖼️ بهبود عکس
# ═══════════════════════════════════════

async def improve_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🖼️ بهبود عکس\n\n"

        "عکس موردنظرت رو ارسال کن و توضیح بده چه تغییری می‌خوای.\n\n"

        "مثلاً:\n"
        "✨ افزایش کیفیت\n"
        "🧹 حذف پس‌زمینه\n"
        "🎨 تغییر سبک\n"
        "💡 بهتر کردن نور\n\n"

        "🔜 برای ویرایش واقعی تصویر باید سرویس پردازش تصویر "
        "به ربات متصل بشه.",

        reply_markup=main_keyboard()

    )


# ═══════════════════════════════════════
# 🔗 تحلیل لینک
# ═══════════════════════════════════════

async def analyze_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🔗 تحلیل لینک\n\n"

        "لینک موردنظرت رو ارسال کن.\n\n"

        "می‌تونیم در نسخه‌های بعدی قابلیت‌هایی مثل:\n"

        "📱 تحلیل لینک اینستاگرام\n"
        "🎵 استخراج اطلاعات موسیقی\n"
        "🎬 شناسایی محتوای ویدئو\n"
        "📝 خلاصه‌سازی صفحه\n\n"

        "رو به ربات اضافه کنیم.",

        reply_markup=main_keyboard()

    )


# ═══════════════════════════════════════
# ℹ️ درباره دستیار
# ═══════════════════════════════════════

async def about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "✨ درباره دستیار هوشمند ✨\n\n"

        "🤖 یک دستیار چندمنظوره برای انجام کارهای مختلف.\n\n"

        "💬 گفتگو با AI\n"
        "🧠 پاسخ به سؤالات\n"
        "🎵 موسیقی\n"
        "🎬 فیلم و سریال\n"
        "🖼️ تصویر\n"
        "🔗 لینک‌ها\n"
        "💻 برنامه‌نویسی\n"
        "📚 آموزش\n\n"

        "🚀 قابلیت‌های جدید به‌مرور اضافه خواهند شد.",

        reply_markup=main_keyboard()

    )


# ═══════════════════════════════════════
# 🔄 شروع دوباره
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
# 📨 پردازش پیام‌ها
# ═══════════════════════════════════════

async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    user_id = update.effective_user.id


    if text == "🤖 گفت‌وگو با AI":

        await start_ai(
            update,
            context
        )

        return


    if text == "🧠 ابزارهای هوشمند":

        await smart_tools(
            update,
            context
        )

        return


    if text == "🎵 تشخیص آهنگ":

        await music_finder(
            update,
            context
        )

        return


    if text == "🎬 پیدا کردن فیلم":

        await movie_finder(
            update,
            context
        )

        return


    if text == "🖼️ بهبود عکس":

        await improve_photo(
            update,
            context
        )

        return


    if text == "🔗 تحلیل لینک":

        await analyze_link(
            update,
            context
        )

        return


    if text == "ℹ️ درباره دستیار":

        await about(
            update,
            context
        )

        return


    if text == "🔄 شروع دوباره":

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

        "👇 یکی از گزینه‌های منو رو انتخاب کن:",

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

        "🤖 Smart AI Assistant is running..."

    )


    app.run_polling()


# ═══════════════════════════════════════
# ▶️ شروع برنامه
# ═══════════════════════════════════════

if __name__ == "__main__":

    main()
