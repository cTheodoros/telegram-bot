import asyncio
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from aiohttp import web
import logging
import signal
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot manager to avoid global variables
class BotManager:
    def __init__(self):
        self.bot_app = None

    async def initialize(self, token):
        self.bot_app = ApplicationBuilder().token(token).build()
        self.bot_app.add_handler(CommandHandler("start", start))
        self.bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        logger.info("Bot initialized")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot started! Send 1572 or 1455 to test.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    logger.info(f"Received message: {message}")
    if message == "1572":
        await update.message.reply_text("greșit")
    elif message == "1455":
        await update.message.reply_text("bravo")
    else:
        await update.message.reply_text("Mesaj necunoscut. Încearcă din nou!")

async def webhook(request):
    bot_manager = request.app['BOT_MANAGER']
    try:
        # Verify secret token for security
        secret_token = os.getenv("WEBHOOK_SECRET_TOKEN")
        if secret_token and request.headers.get('X-Telegram-Bot-Api-Secret-Token') != secret_token:
            logger.warning("Unauthorized webhook request")
            return web.Response(text='Unauthorized', status=403)
        
        data = await request.json()
        update = Update.de_json(data, bot_manager.bot_app.bot)
        if update:
            await bot_manager.bot_app.process_update(update)
        return web.Response(text='OK', status=200)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return web.Response(text='Error', status=500)

async def set_webhook(bot_manager, webhook_url, secret_token=None):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            await bot_manager.bot_app.bot.set_webhook(
                url=webhook_url,
                secret_token=secret_token,
                drop_pending_updates=True  # Ensure no pending updates cause polling issues
            )
            logger.info(f"Webhook set successfully: {webhook_url}")
            return
        except Exception as e:
            logger.error(f"Failed to set webhook (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.critical("Failed to set webhook after retries")
                raise

async def shutdown(runner, bot_manager):
    logger.info("Shutting down...")
    try:
        await bot_manager.bot_app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted")
    except Exception as e:
        logger.error(f"Failed to delete webhook: {e}")
    await runner.cleanup()
    logger.info("Server stopped")

async def health_check(request):
    return web.Response(text="OK", status=200)

async def main():
    bot_manager = BotManager()
    token = os.getenv("TOKEN")
    if not token:
        logger.critical("TOKEN environment variable not set")
        raise ValueError("TOKEN environment variable not set")

    webhook_url = os.getenv("WEBHOOK_URL", "https://telegram-bot-tedk.onrender.com/webhook")
    secret_token = os.getenv("WEBHOOK_SECRET_TOKEN")

    await bot_manager.initialize(token)

    aio_app = web.Application()
    aio_app['BOT_MANAGER'] = bot_manager
    aio_app.router.add_post('/webhook', webhook)
    aio_app.router.add_get('/health', health_check)

    await set_webhook(bot_manager, webhook_url, secret_token)

    runner = web.AppRunner(aio_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()
    logger.info(f"Webhook server started on port {os.getenv('PORT', 8080)}")

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await shutdown(runner, bot_manager)

def handle_shutdown(loop, runner, bot_manager):
    loop.run_until_complete(shutdown(runner, bot_manager))
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
    sys.exit(0)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    bot_manager = BotManager()
    runner = None

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda: handle_shutdown(loop, runner, bot_manager)
        )

    try:
        runner = loop.run_until_complete(main())
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        if runner:
            loop.run_until_complete(shutdown(runner, bot_manager))
        sys.exit(1)
