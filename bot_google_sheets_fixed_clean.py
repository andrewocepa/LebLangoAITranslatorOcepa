
import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Conversation states
CHOOSE_DIRECTION, FIRST_SENTENCE, SECOND_SENTENCE = range(3)

# Google Sheets setup with private_key line fix
# def append_to_sheet(lango, english):
#     scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#     creds_dict = json.loads(os.getenv("GOOGLE_CREDS"))
#     creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n").replace("\n", "
# ")
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open("Lango-English Dataset").sheet1
#     sheet.append_row([lango, english])
def append_to_sheet(lango, english):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.getenv("GOOGLE_CREDS"))
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")  # 🔥 this is the correct line
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Lango-English Dataset").sheet1
    sheet.append_row([lango, english])

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Lango", "English"]]
    await update.message.reply_text(
        "👋 Welcome! / Ojoli!\n"
        "Let’s collect Lango ↔ English sentence pairs. / Kong Oraa kop iLebLango kede agonyere iLebMunu.\n"
        "Please choose the language : / Yer leb :",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSE_DIRECTION

# Capture direction
async def choose_direction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = update.message.text.lower()
    if lang not in ["lango", "english"]:
        await update.message.reply_text("Please choose either Lango or English. / Yer Leblango onyo Lebmunu.")
        return CHOOSE_DIRECTION

    context.user_data["direction"] = lang
    await update.message.reply_text(f"Enter the sentence here in {lang.capitalize()}:\n"
                                    f"Coo kopono kan i {lang.capitalize()}.")
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
    else:
        lango, english = target, source

    append_to_sheet(lango, english)

    await update.message.reply_text("✅ Sentence saved! / Kube kicoko!\n"
                                    "Would you like to submit another? (yes/no) / Imito cwalo en okene?")
    return CHOOSE_DIRECTION

# Handle stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("👋 Thank you for your help! / Apwoyo konyi!")
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
