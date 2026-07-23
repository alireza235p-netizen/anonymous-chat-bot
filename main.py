import os
import logging
import random
from datetime import datetime, timezone

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
    ConversationHandler,
    filters,
)

from supabase import create_client, Client


# ═══════════════════════════════════════
# ⚙️ تنظیمات
# ═══════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
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

# وضعیت تکمیل پروفایل
profile_states = {}


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

    try:

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
            "last_seen": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        supabase.table("users").insert(
            new_user
        ).execute()

        return new_user

    except Exception as error:

        logging.error(
            f"خطا در دریافت کاربر: {error}"
        )

        return None


# ═══════════════════════════════════════
# 🪙 تغییر موجودی سکه
# ═══════════════════════════════════════

def change_coins(
    user_id,
    amount,
    transaction_type,
    description
):

    user = get_user(user_id)

    if not user:
        return False

    current_coins = user.get("coins") or 0

    new_coins = current_coins + amount

    if new_coins < 0:
        return False

    try:

        (
            supabase
            .table("users")
            .update({
                "coins": new_coins
            })
            .eq("id", user_id)
            .execute()
        )

        transaction = {
            "user_id": user_id,
            "amount": amount,
            "type": transaction_type,
            "description": description,
        }

        supabase.table(
            "coin_transactions"
        ).insert(
            transaction
        ).execute()

        return True

    except Exception as error:

        logging.error(
            f"خطا در تغییر سکه: {error}"
        )

        return False


# ═══════════════════════════════════════
# 🚀 شروع ربات
# ═══════════════════════════════════════

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    get_user(user.id)

    await update.message.reply_text(

        f"🌈 سلام {user.first_name} عزیز! 😍\n\n"

        "🎉 به دنیای چت ناشناس خوش اومدی!\n\n"

        "💬 اینجا می‌تونی با آدم‌های جدید آشنا بشی.\n"
        "🎲 جستجوی شانسی کاملاً رایگانه!\n\n"

        "👇 از منوی پایین انتخاب کن:",

        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 🪙 موجودی سکه
# ═══════════════════════════════════════

async def balance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = get_user(
        update.effective_user.id
    )

    coins = (
        user.get("coins", 0)
        if user
        else 0
    )

    await update.message.reply_text(

        "🪙 موجودی شما\n\n"

        f"✨ {coins} سکه\n\n"

        "💡 با دعوت دوستان می‌تونی سکه رایگان بگیری.",

        reply_markup=main_keyboard()
    )


# ═══════════════════════════════════════
# 👤 نمایش پروفایل
# ═══════════════════════════════════════

async def profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    user = get_user(user_id)

    if not user:

        await update.message.reply_text(
            "❌ خطایی در دریافت پروفایل رخ داد."
        )

        return

    photo_id = user.get("photo_id")

    first_name = (
        user.get("first_name")
        or "ثبت نشده"
    )

    age = (
        user.get("age")
        or "ثبت نشده"
    )

    gender = (
        user.get("gender")
        or "ثبت نشده"
    )

    province = (
        user.get("province")
        or "ثبت نشده"
    )

    city = (
        user.get("city")
        or "ثبت نشده"
    )

    bio = (
        user.get("bio")
        or "بیوگرافی ثبت نشده"
    )

    likes_count = (
        user.get("likes")
        or 0
    )

    coins = (
        user.get("coins")
        or 0
    )

    profile_text = (

        "👤 پروفایل من\n\n"

        f"📛 نام: {first_name}\n"
        f"🎂 سن: {age}\n"
        f"🚻 جنسیت: {gender}\n"
        f"📍 استان: {province}\n"
        f"🏙️ شهر: {city}\n\n"

        f"📝 بیو:\n{bio}\n\n"

        f"❤️ لایک‌ها: {likes_count}\n"
        f"🪙 سکه: {coins}\n"
    )

    if photo_id:

        await update.message.reply_photo(

            photo=photo_id,

            caption=profile_text,

            reply_markup=main_keyboard()
        )

    else:

        await update.message.reply_text(

            profile_text
            + "\n📸 عکس: ثبت نشده",

            reply_markup=main_keyboard()
        )


# ═══════════════════════════════════════
# ✏️ شروع تکمیل پروفایل
# ═══════════════════════════════════════

async def edit_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    profile_states[user_id] = {
        "step": "photo",
        "data": {}
    }

    await update.message.reply_text(

        "👤 تکمیل پروفایل\n\n"

        "📸 لطفاً یک عکس برای پروفایلت بفرست.\n\n"

        "⚠️ برای لغو، بنویس: لغو",

        reply_markup=ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton("❌ لغو")
                ]
            ],
            resize_keyboard=True
        )
    )


# ═══════════════════════════════════════
# 📸 دریافت عکس پروفایل
# ═══════════════════════════════════════

async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    state = profile_states.get(user_id)

    if not state:
        return

    if state["step"] != "photo":
        return

    photo = update.message.photo[-1]

    photo_id = photo.file_id

    state["data"]["photo_id"] = photo_id

    state["step"] = "name"

    await update.message.reply_text(

        "✅ عکس دریافت شد.\n\n"

        "📛 حالا اسمت رو بفرست:"

    )


# ═══════════════════════════════════════
# 📝 پردازش اطلاعات پروفایل
# ═══════════════════════════════════════

async def handle_profile_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    state = profile_states.get(user_id)

    if not state:
        return False

    text = update.message.text.strip()

    if text == "❌ لغو" or text == "لغو":

        profile_states.pop(
            user_id,
            None
        )

        await update.message.reply_text(

            "❌ تکمیل پروفایل لغو شد.",

            reply_markup=main_keyboard()
        )

        return True

    step = state["step"]

    if step == "name":

        state["data"]["first_name"] = text

        state["step"] = "age"

        await update.message.reply_text(
            "🎂 سنت رو وارد کن:"
        )

        return True

    if step == "age":

        if not text.isdigit():

            await update.message.reply_text(
                "❌ سن باید عدد باشه."
            )

            return True

        age = int(text)

        if age < 13 or age > 100:

            await update.message.reply_text(
                "❌ سن واردشده معتبر نیست."
            )

            return True

        state["data"]["age"] = age

        state["step"] = "gender"

        await update.message.reply_text(

            "🚻 جنسیتت رو وارد کن:\n\n"

            "👨 پسر\n"
            "👩 دختر"

        )

        return True

    if step == "gender":

        state["data"]["gender"] = text

        state["step"] = "province"

        await update.message.reply_text(
            "📍 اسم استانت رو وارد کن:"
        )

        return True

    if step == "province":

        state["data"]["province"] = text

        state["step"] = "city"

        await update.message.reply_text(
            "🏙️ اسم شهرت رو وارد کن:"
        )

        return True

    if step == "city":

        state["data"]["city"] = text

        state["step"] = "bio"

        await update.message.reply_text(

            "📝 حالا یک بیو کوتاه برای پروفایلت بنویس:\n\n"

            "مثلاً:\n"
            "🎮 عاشق بازی و فیلمم\n"
            "🎵 موسیقی گوش میدم"

        )

        return True

    if step == "bio":

        state["data"]["bio"] = text

        data = state["data"]

        try:

            user = get_user(user_id)

            already_rewarded = (
                user.get(
                    "profile_reward_claimed"
                )
                if user
                else False
            )

            update_data = {

                "photo_id":
                    data.get("photo_id"),

                "first_name":
                    data.get("first_name"),

                "age":
                    data.get("age"),

                "gender":
                    data.get("gender"),

                "province":
                    data.get("province"),

                "city":
                    data.get("city"),

                "bio":
                    data.get("bio"),

                "completed_profile":
                    True,
            }

            if not already_rewarded:

                update_data[
                    "profile_reward_claimed"
                ] = True

            (
                supabase
                .table("users")
                .update(update_data)
                .eq("id", user_id)
                .execute()
            )

            if not already_rewarded:

                change_coins(

                    user_id,

                    5,

                    "profile_reward",

                    "پاداش تکمیل پروفایل"
                )

                reward_message = (
                    "\n\n🎁 ۵ سکه بابت تکمیل پروفایل گرفتی!"
                )

            else:

                reward_message = ""

            profile_states.pop(
                user_id,
                None
            )

            await update.message.reply_text(

                "🎉 پروفایلت با موفقیت تکمیل شد!\n\n"

                "📸 عکس ذخیره شد.\n"
                "👤 اطلاعاتت ثبت شد.\n"
                "📝 بیوت ثبت شد."

                + reward_message,

                reply_markup=main_keyboard()
            )

            return True

        except Exception as error:

            logging.error(error)

            await update.message.reply_text(

                "❌ ذخیره پروفایل انجام نشد.\n"
                "لطفاً دوباره تلاش کن."
            )

            return True

    return False


# ═══════════════════════════════════════
# 🎲 جستجوی شانسی
# ═══════════════════════════════════════

async def random_search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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

        partner = random.choice(
            waiting_users
        )

        waiting_users.remove(
            partner
        )

        active_chats[user_id] = partner

        active_chats[partner] = user_id

        now = datetime.now(
            timezone.utc
        )

        chat_started_at[user_id] = now

        chat_started_at[partner] = now

        message = (

            "🎉 مخاطب پیدا شد!\n\n"

            "💬 حالا می‌تونید ناشناس "
            "با هم صحبت کنید.\n\n"

            "👤 برای دیدن پروفایل طرف مقابل "
            "از گزینه پروفایل استفاده کنید.\n\n"

            "⏱️ حداقل ۱۲ ثانیه فرصت دارید."
        )

        await context.bot.send_message(
            user_id,
            message,
            reply_markup=main_keyboard()
        )

        await context.bot.send_message(
            partner,
            message,
            reply_markup=main_keyboard()
        )

    else:

        waiting_users.append(
            user_id
        )

        await update.message.reply_text(

            "🔎 در حال پیدا کردن "
            "یک مخاطب
