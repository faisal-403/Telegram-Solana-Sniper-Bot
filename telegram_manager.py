import logging
import time
from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from typing import Set, Dict

class TelegramManager:
    def __init__(self, config, monitor):
        self.config = config
        self.monitor = monitor
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.authenticated_users: Set[int] = set()
        self.password_attempts: Dict[int, int] = {}
        self.application = None
        self.bot = None
        self.logger = logging.getLogger(__name__)

    async def authenticate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not context.args:
            await update.message.reply_text("🔒 Usage: /password YOUR_PASSWORD")
            return
            
        password = ' '.join(context.args)
        if password == self.config.BOT_PASSWORD:
            self.authenticated_users.add(user_id)
            await update.message.reply_text("✅ Authentication successful!")
        else:
            await update.message.reply_text("❌ Incorrect password")

    def _is_authenticated(self, user_id: int) -> bool:
        return user_id in self.authenticated_users

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if self._is_authenticated(user.id):
            await update.message.reply_text("✅ You're authenticated!")
        else:
            await update.message.reply_text("🔒 Please authenticate with /password")

    async def send_notification(self, message: str):
        if self.bot and self.chat_id:
            try:
                await self.bot.send_message(chat_id=self.chat_id, text=message)
            except Exception as e:
                self.logger.error(f"Failed to send notification: {e}")

    def setup_handlers(self, application: Application):
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("password", self.authenticate))

    async def initialize(self):
        self.application = Application.builder().token(self.bot_token).build()
        self.bot = self.application.bot
        self.setup_handlers(self.application)
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def shutdown(self):
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
