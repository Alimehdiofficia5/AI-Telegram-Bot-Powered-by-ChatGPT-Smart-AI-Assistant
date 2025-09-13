import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI, OpenAIError
import asyncio

# =========================
# 🔑 Keys
# =========================
OPENAI_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8304673595:AAEslxwdshpSZOL-0BEEkMBi9rcwOjvdrzY"

# =========================
# ⚙️ Model & OpenRouter Settings
# =========================
MODEL_NAME = "openai/gpt-3.5-turbo"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_HEADERS = {
    "HTTP-Referer": "https://t.me/your_bot_username",
    "X-Title": "Ali Telegram AI Bot",
}

# =========================
# 📜 Logging Settings
# =========================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("ali_telegram_ai_bot")

# =========================
# 🤖 OpenAI (OpenRouter) Client Init
# =========================
client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENAI_API_KEY,
    default_headers=DEFAULT_HEADERS
)

# =========================
# 🔁 API Call with retries
# =========================
async def generate_reply(messages, model=MODEL_NAME, retries=3, backoff=1):
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"🔌 Calling OpenRouter (Attempt {attempt})")
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=400
            )
            reply = resp.choices[0].message.content.strip()
            logger.info(f"✅ Reply: {reply[:100]}...")
            return reply
        except OpenAIError as e:
            logger.error(f"⚠️ OpenAIError: {str(e)}")
            if attempt == retries:
                raise
        except Exception as e:
            logger.error(f"❌ Unexpected Error: {str(e)}")
            if attempt == retries:
                raise
        logger.info(f"⏳ Retrying in {backoff}s...")
        await asyncio.sleep(backoff)
        backoff *= 2

# =========================
# 📌 Reply Keyboard
# =========================
main_keyboard = ReplyKeyboardMarkup(
    [
        ["💬 Chat", "ℹ️ About"],
        ["🛠 Change Model", "❌ Stop Bot"]
    ],
    resize_keyboard=True
)

# =========================
# /start Command
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"👋 User {user.first_name} started the bot.")
    await update.message.reply_text(
        f"**ہیلو {user.first_name}!** 👋\n\n"
        f"میں آپ کا **AI بوٹ** ہوں۔ آپ مجھ سے سوال پوچھ سکتے ہیں، آئیڈیاز لے سکتے ہیں، یا چیٹ کر سکتے ہیں۔\n\n"
        f"📌 **نیچے دیے گئے بٹن استعمال کریں:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard
    )

# =========================
# Chat Handler
# =========================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = update.message.text
    logger.info(f"📩 Message from {user.first_name}: {user_message}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_message}
    ]

    try:
        reply_text = await generate_reply(messages)
        await update.message.reply_text(f"**🤖 AI:** {reply_text}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        error_msg = f"⚠️ Error: {str(e)}"
        logger.error(error_msg)
        await update.message.reply_text(error_msg)

# =========================
# Main Function
# =========================
def main():
    logger.info("🚀 Starting Telegram AI Bot...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    logger.info("✅ Bot is now running. Waiting for messages...")
    app.run_polling()

if __name__ == "__main__":
    main()
