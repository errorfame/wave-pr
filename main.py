from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.error import TelegramError
import logging
from config import load_config
from handlers import user_handlers, admin_handlers
from database import Database
from utils.logger import logger, log_message
from utils.rate_limiter import RateLimiter
from datetime import datetime
from keyboards import get_main_keyboard

# Создаем глобальный rate limiter
rate_limiter = RateLimiter(
    messages_per_minute=20,  # максимум сообщений в минуту
    max_similar_messages=5,   # максимум одинаковых сообщений подряд
    block_duration_minutes=5  # длительность блокировки
)

async def check_rate_limit(update: Update) -> bool:
    """Проверяет ограничения отправки сообщений"""
    user = update.effective_user
    message_text = update.message.text if update.message else ""
    
    can_send, error_message = rate_limiter.can_send_message(user.id, message_text)
    if not can_send:
        try:
            await update.message.reply_text(error_message)
        except TelegramError:
            pass
        log_message(user.id, user.username or "Unknown", "spam", "Сработала защита от спама", error_message)
        return False
    return True

async def message_handler_with_spam_protection(update: Update, context: ContextTypes.DEFAULT_TYPE, handler):
    """Обертка для обработчиков сообщений с защитой от спама"""
    if not await check_rate_limit(update):
        return
    return await handler(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    user = update.effective_user if update else None
    if user:
        log_message(
            user.id,
            user.username or "Unknown",
            "error",
            "Произошла ошибка в боте",
            str(context.error)
        )
    else:
        logger.error(f"Произошла ошибка: {str(context.error)}")

def main():
    # Загрузка конфигурации
    config = load_config()
    
    # Создание приложения
    application = Application.builder().token(config.token).build()
    
    # Сохранение конфигурации в bot_data для доступа из хэндлеров
    application.bot_data['config'] = config
    
    # Отключаем все предупреждения
    logging.getLogger('telegram').setLevel(logging.ERROR)
    logging.getLogger('telegram.ext.conversationhandler').setLevel(logging.ERROR)
    
    # Регистрация основных обработчиков команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("about", user_handlers.show_about))
    application.add_handler(CommandHandler("vacancies", user_handlers.show_vacancies))
    application.add_handler(CommandHandler("applications", user_handlers.show_applications))
    
    # Обработчик добавления вакансии для админов
    add_vacancy_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                admin_handlers.start_add_vacancy,
                pattern=r'^add_vacancy$'
            )
        ],
        states={
            admin_handlers.AWAITING_TITLE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    admin_handlers.process_vacancy_title
                )
            ],
            admin_handlers.AWAITING_DESCRIPTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    admin_handlers.process_vacancy_description
                )
            ],
            admin_handlers.AWAITING_IMAGE: [
                MessageHandler(
                    filters.PHOTO,
                    admin_handlers.process_vacancy_image
                ),
                CallbackQueryHandler(
                    admin_handlers.skip_image,
                    pattern=r'^skip_image$'
                )
            ]
        },
        fallbacks=[
            CallbackQueryHandler(
                admin_handlers.show_admin_panel,
                pattern=r'^admin_panel$'
            )
        ],
        per_chat=True,
        per_user=True
    )
    
    # Обработчик редактирования вакансий
    edit_vacancy_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                admin_handlers.start_edit_title,
                pattern=r'^edit_title_\d+$'
            ),
            CallbackQueryHandler(
                admin_handlers.start_edit_description,
                pattern=r'^edit_description_\d+$'
            )
        ],
        states={
            admin_handlers.EDIT_TITLE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    admin_handlers.process_edit_title
                )
            ],
            admin_handlers.EDIT_DESCRIPTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    admin_handlers.process_edit_description
                )
            ]
        },
        fallbacks=[
            CallbackQueryHandler(
                admin_handlers.cancel_edit,
                pattern=r'^cancel_edit_\d+$'
            ),
            CallbackQueryHandler(
                admin_handlers.edit_vacancy,
                pattern=r'^edit_vacancy_\d+$'
            )
        ],
        per_chat=True,
        per_user=True
    )
    
    # Обработчик отклика на вакансию
    apply_vacancy_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                user_handlers.apply_to_vacancy,
                pattern=r'^apply_\d+$'
            )
        ],
        states={
            user_handlers.AWAITING_APPLICATION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    user_handlers.process_application
                )
            ]
        },
        fallbacks=[
            CallbackQueryHandler(
                user_handlers.back_to_vacancies,
                pattern=r'^back_to_vacancies$'
            )
        ],
        per_chat=True,
        per_user=True
    )
    
    # Регистрация обработчиков диалогов (должны быть перед общими обработчиками)
    application.add_handler(add_vacancy_conv)
    application.add_handler(apply_vacancy_conv)
    application.add_handler(edit_vacancy_conv)
    
    # Регистрация обработчиков текстовых команд меню
    for pattern, handler in [
        ('^📋 Вакансии$', user_handlers.show_vacancies),
        ('^📝 Мои заявки$', user_handlers.show_applications),
        ('^ℹ️ О боте$', user_handlers.show_about)
    ]:
        application.add_handler(MessageHandler(
            filters.Regex(pattern),
            lambda u, c, h=handler: message_handler_with_spam_protection(u, c, h)
        ))
    
    # Обработчики callback кнопок для админа
    application.add_handler(CallbackQueryHandler(
        admin_handlers.show_admin_panel,
        pattern=r'^admin_panel$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_handlers.show_vacancies_for_edit,
        pattern=r'^edit_vacancies$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_handlers.back_to_main,
        pattern=r'^back_to_main$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_handlers.edit_vacancy,
        pattern=r'^edit_vacancy_\d+$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_handlers.toggle_vacancy_status,
        pattern=r'^toggle_status_\d+$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_handlers.delete_vacancy,
        pattern=r'^delete_vacancy_\d+$'
    ))
    application.add_handler(CallbackQueryHandler(
        admin_handlers.process_application_response,
        pattern=r'^application_(accept|reject)_\d+$'
    ))
    
    # Обработчики callback кнопок для пользователя
    application.add_handler(CallbackQueryHandler(
        user_handlers.show_vacancy,
        pattern=r'^vacancy_\d+$'
    ))
    application.add_handler(CallbackQueryHandler(
        user_handlers.back_to_vacancies,
        pattern=r'^back_to_vacancies$'
    ))
    
    # Обработчик неизвестных команд (должен быть после всех команд)
    application.add_handler(MessageHandler(
        filters.COMMAND,
        user_handlers.unknown_command
    ))
    
    # Обработчик неизвестных сообщений (должен быть последним)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        lambda u, c: message_handler_with_spam_protection(u, c, user_handlers.handle_text)
    ))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info(str({
        'type': 'start',
        'user': 'System',
        'action': 'Бот запущен и готов к работе'
    }))
    
    # Запуск бота
    application.run_polling()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с проверкой на администратора"""
    user_id = update.effective_user.id
    db = Database()
    
    if db.is_admin(user_id):
        return await admin_handlers.admin_start(update, context)
    return await user_handlers.start(update, context)

if __name__ == '__main__':
    main()
