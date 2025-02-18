from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import logging
from database import Database
from utils.logger import log_message

logger = logging.getLogger(__name__)

def admin_only(func):
    """Декоратор для проверки прав администратора"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        username = update.effective_user.username or "Неизвестный пользователь"
        
        db = Database()
        if not db.is_admin(user_id):
            log_message(user_id, username, "error", "Попытка доступа к админке", "Доступ запрещен")
            await update.message.reply_text("Извините, у вас нет доступа к этой команде.")
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapped
