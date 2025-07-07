import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

# Apply nest_asyncio to allow running in environments with an existing event loop
nest_asyncio.apply()

async def handle_message(update: Update, context):
    message = update.message.text.strip()
    print(f"Received message: {message}")
    if message == "1572":
        await update.message.reply_text("greșit")
    elif message == "1455":
        await update.message.reply_text("bravo")
    else:
        await update.message.reply_text("Mesaj necunoscut. Încearcă din nou!")

async def main():
    # Replace with your actual bot token
    app = ApplicationBuilder().token("7798512073:AAF99ZGp1-ZqnncYxTsytx7deDdOw_VAdik").build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is starting...")

    # Start the bot with run_polling
    try:
        await app.run_polling()  # This starts polling and keeps the bot running
    except KeyboardInterrupt:
        print("Bot is stopping...")
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    # Run the main coroutine and keep the event loop alive
    asyncio.run(main())
