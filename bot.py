
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import csv

# Conversation states
CHOOSE_DIRECTION, FIRST_SENTENCE, SECOND_SENTENCE = range(3)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Lango", "English"]]
    await update.message.reply_text(
        "👋 Welcome! / Wajoli!\n"
        "Let’s collect Lango ↔ English sentence pairs. / Wan otimo kube me cik Lango ki English.\n"
        "Please choose the language of your sentence: / Yer leb me nyinge:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSE_DIRECTION

# Capture direction
async def choose_direction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = update.message.text.lower()
    if lang not in ["lango", "english"]:
        await update.message.reply_text("Please choose either Lango or English. / Yer Lango onyo English.")
        return CHOOSE_DIRECTION

    context.user_data["direction"] = lang
    await update.message.reply_text(f"Enter your sentence in {lang.capitalize()}:\n"
                                    f"Cwaa nying i {lang.capitalize()}.")
    return FIRST_SENTENCE

# Get source sentence
async def get_first_sentence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["source_sentence"] = update.message.text
    direction = context.user_data["direction"]
    target_lang = "English" if direction == "lango" else "Lango"
    await update.message.reply_text(f"Now enter the translation in {target_lang}:\n"
                                    f"Cwaa kube i {target_lang}.")
    return SECOND_SENTENCE

# Get translation and save
async def get_second_sentence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    source = context.user_data["source_sentence"]
    target = update.message.text
    direction = context.user_data["direction"]

    if direction == "lango":
        lango, english = source, target
        dir_label = "Lango→English"
    else:
        lango, english = target, source
        dir_label = "English→Lango"

    with open("lango_english_dataset.csv", "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([lango, english, dir_label])

    await update.message.reply_text("✅ Sentence saved! / Kube kicoko!\n"
                                    "Would you like to submit another? (yes/no) / I mito cwaa mukene?")
    return CHOOSE_DIRECTION

# Handle stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("👋 Thank you for your help! / Apwoyo keni!")
    return ConversationHandler.END

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_DIRECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_direction)],
            FIRST_SENTENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_first_sentence)],
            SECOND_SENTENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_second_sentence)],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
