except Exception as error:

        logging.error(
            f"OPENAI_ERROR: {type(error).__name__} | {str(error)}"
        )

        await update.message.reply_text(

            f"❌ خطای واقعی اتصال به هوش مصنوعی:\n\n"
            f"نوع خطا: {type(error).__name__}\n"
            f"جزئیات: {str(error)}",

            reply_markup=main_keyboard()

        )
