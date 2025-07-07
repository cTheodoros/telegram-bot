import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from flask import Flask, request
import json

# Initialize Flask app
app = Flask(__name__)

# Store the bot application globally
bot_app = None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    print(f"Received message: {message}")
    if message == "1572":
        await update.message.reply_text("greșit")
    elif message == "1455":
        await update.message.reply_text("bravo")
    else:
        await update.message.reply_text("Mesaj necunoscut. Încearcă din nou!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot started! Send 1572 or 1455 to test.")

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(json.loads(request.get_data(as_text=True)), bot_app.bot)
    # Run the update processing in the existing event loop
    asyncio.get_event_loop().create_task(bot_app.process_update(update))
    return 'OK', 200

async def main():
    global bot_app
    # Use environment variable for token
    import os
    token = os.getenv("TOKEN")
    if not token:
        raise ValueError("TOKEN environment variable not set")
    
    bot_app = ApplicationBuilder().token(token).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is starting...")

    # Set webhook
    webhook_url = "https://telegram-bot-tedk.onrender.com/webhook"  # Verifică dacă URL-ul este corect
    try:
        await bot_app.bot.set_webhook(url=webhook_url)
        print("Webhook set successfully")
    except Exception as e:
        print(f"Failed to set webhook: {e}")
        raise

if __name__ == '__main__':
    # Initialize bot
    asyncio.run(main())
    # Run Flask app
    app.run(host='0.0.0.0', port=8080)