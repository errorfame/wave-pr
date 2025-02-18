import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram import Update
from telegram.ext import ContextTypes
from config import load_config
from handlers import user_handlers, admin_handlers
from database import Database
from utils.logger import logger, log_message

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
    
    # Регистрация обработчиков текстовых команд
    application.add_handler(MessageHandler(
        filters.Regex('^📋 Вакансии$'),
        user_handlers.show_vacancies
    ))
    application.add_handler(MessageHandler(
        filters.Regex('^📝 Мои заявки$'),
        user_handlers.show_applications
    ))
    application.add_handler(MessageHandler(
        filters.Regex('^ℹ️ О боте$'),
        user_handlers.show_about
    ))
    
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
            ]
        },
        fallbacks=[
            CallbackQueryHandler(
                admin_handlers.show_admin_panel,
                pattern=r'^admin_panel$'
            )
        ]
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
        fallbacks=[]
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
                pattern=r'^edit_desc_\d+$'
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
            )
        ]
    )
    
    # Регистрация основных обработчиков
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("about", user_handlers.show_about))
    application.add_handler(CommandHandler("vacancies", user_handlers.show_vacancies))
    application.add_handler(CommandHandler("applications", user_handlers.show_applications))
    
    # Регистрация обработчиков диалогов
    application.add_handler(add_vacancy_conv)
    application.add_handler(apply_vacancy_conv)
    application.add_handler(edit_vacancy_conv)
    
    # Обработчики кнопок
    application.add_handler(CallbackQueryHandler(
        user_handlers.show_vacancy,
        pattern=r'^vacancy_\d+$'
    ))
    application.add_handler(CallbackQueryHandler(
        user_handlers.back_to_vacancies,
        pattern=r'^back_to_vacancies$'
    ))
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
    
    # Обработчик неизвестных команд (должен быть последним)
    application.add_handler(MessageHandler(
        filters.COMMAND,
        user_handlers.unknown_command
    ))
    
    # Обработчик неизвестных сообщений
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        user_handlers.handle_text
    ))
    
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
