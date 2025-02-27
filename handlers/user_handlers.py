from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import Database
from keyboards import (
    get_vacancies_keyboard, get_vacancy_actions_keyboard,
    get_back_to_list_keyboard, get_main_keyboard,
    get_back_to_main_keyboard
)
import messages
from utils.logger import log_message
from datetime import datetime

# Состояния для ConversationHandler
AWAITING_APPLICATION = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start для обычных пользователей"""
    user = update.effective_user
    log_message(user.id, user.username or "Unknown", "start", "Запустил бота")
    
    db = Database()
    vacancies = db.get_active_vacancies()
    
    # Создаем клавиатуру с вакансиями по 2 в строку
    keyboard = []
    row = []
    for i, vacancy in enumerate(vacancies, 1):
        status = "🟢" if vacancy.is_active else "🔴"
        row.append(
            InlineKeyboardButton(
                f"{status} {vacancy.title}",
                callback_data=f"vacancy_{vacancy.id}"
            )
        )
        
        # После каждых двух кнопок или в конце списка создаем новую строку
        if len(row) == 2 or i == len(vacancies):
            keyboard.append(row)
            row = []
    
    # Формируем сообщение
    message_text = messages.START_MESSAGE
    if vacancies:
        message_text += "\n\n📋 *Доступные вакансии:*"
    else:
        message_text += "\n\n❗️ *Нет активных вакансий*"
    
    # Отправляем сообщение с основной клавиатурой и инлайн-кнопками
    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    
    # Показываем основную клавиатуру отдельным действием
    await update.message.reply_text(
        "Используйте меню для навигации:",
        reply_markup=get_main_keyboard()
    )

async def show_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает подробную информацию о вакансии"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    vacancy_id = int(query.data.split('_')[1])
    
    log_message(user.id, user.username or "Unknown", "view", "Просмотрел вакансию", f"ID: {vacancy_id}")
    
    db = Database()
    vacancy = db.get_vacancy(vacancy_id)
    
    if not vacancy:
        await query.message.edit_text(
            "❌ Вакансия не найдена или была удалена.",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, может ли пользователь откликнуться
    can_apply = db.can_apply_to_vacancy(user.id, vacancy_id)
    
    # Создаем клавиатуру
    keyboard = []
    row = []
    
    # Кнопка "Откликнуться" только если можно
    if can_apply and vacancy.is_active:
        row.append(
            InlineKeyboardButton(
                "💼 Откликнуться",
                callback_data=f"apply_{vacancy_id}"
            )
        )
    
    # Кнопка "Назад" всегда добавляется
    row.append(
        InlineKeyboardButton(
            "« Назад к списку",
            callback_data="back_to_vacancies"
        )
    )
    
    keyboard.append(row)
    
    # Формируем статусное сообщение
    if not vacancy.is_active:
        status_text = "\n\n❌ *Вакансия закрыта*"
    elif not can_apply:
        status_text = "\n\n⏳ *Вы уже откликались на эту вакансию*\nПовторный отклик будет доступен через 24 часа."
    else:
        status_text = ""
    
    try:
        # Если есть изображение, отправляем его с текстом
        if vacancy.image_id:
            await query.message.delete()  # Удаляем старое сообщение
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=vacancy.image_id,
                caption=vacancy.description + (status_text if status_text else ""),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            # Если изображения нет, просто обновляем текст
            await query.message.edit_text(
                vacancy.description + (status_text if status_text else ""),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    except Exception as e:
        log_message(user.id, user.username or "Unknown", "error", "Ошибка при показе вакансии", str(e))
        # Если возникла ошибка с форматированием, отправляем без него
        await query.message.edit_text(
            vacancy.description.replace('*', '') + 
            (status_text.replace('*', '') if status_text else ""),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Назад к списку", callback_data="back_to_vacancies")
            ]])
        )

async def apply_to_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка отклика на вакансию"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    vacancy_id = int(query.data.split('_')[1])
    
    db = Database()
    vacancy = db.get_vacancy(vacancy_id)
    
    if not vacancy:
        # Если вакансия не найдена, отправляем новое сообщение
        await query.message.reply_text(
            messages.ALREADY_APPLIED,
            reply_markup=get_back_to_list_keyboard(),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Проверяем, может ли пользователь откликнуться
    if not db.can_apply_to_vacancy(user.id, vacancy_id):
        log_message(user.id, user.username or "Unknown", "error", "Попытка повторного отклика", f"Вакансия: {vacancy.title}")
        # Отправляем новое сообщение вместо редактирования
        await query.message.reply_text(
            messages.ALREADY_APPLIED,
            reply_markup=get_back_to_list_keyboard(),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    log_message(user.id, user.username or "Unknown", "start", "Начал отклик", f"Вакансия: {vacancy.title}")
    context.user_data['applying_to_vacancy'] = vacancy_id
    
    # Отправляем новое сообщение с инструкциями вместо редактирования
    if vacancy.image_id:
        # Если было сообщение с фото, удаляем его и отправляем новое
        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=messages.APPLY_INSTRUCTIONS,
            reply_markup=get_back_to_list_keyboard(),
            parse_mode='Markdown'
        )
    else:
        # Если было обычное сообщение, редактируем его
        await query.message.edit_text(
            messages.APPLY_INSTRUCTIONS,
            reply_markup=get_back_to_list_keyboard(),
            parse_mode='Markdown'
        )
    
    return AWAITING_APPLICATION

async def process_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка данных, отправленных пользователем"""
    user = update.effective_user
    vacancy_id = context.user_data.get('applying_to_vacancy')
    
    if not vacancy_id:
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте начать сначала.",
            reply_markup=get_back_to_list_keyboard(),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        return ConversationHandler.END
    
    db = Database()
    vacancy = db.get_vacancy(vacancy_id)
    if not vacancy:
        await update.message.reply_text(
            "Вакансия не найдена.",
            reply_markup=get_back_to_list_keyboard(),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        return ConversationHandler.END
    
    application_text = update.message.text
    
    # Добавляем отклик в базу данных
    try:
        application_id = db.add_application(user.id, vacancy_id)
        if not application_id:
            log_message(user.id, user.username or "Unknown", "error", "Ошибка при добавлении отклика", f"Вакансия: {vacancy.title}")
            await update.message.reply_text(
                messages.ALREADY_APPLIED,
                reply_markup=get_back_to_list_keyboard(),
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            return ConversationHandler.END
        
        log_message(user.id, user.username or "Unknown", "success", "Отправил отклик", f"Вакансия: {vacancy.title}")
        
        # Создаем клавиатуру для админов
        keyboard = [
            [
                InlineKeyboardButton("✅ Принять", callback_data=f"application_accept_{application_id}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"application_reject_{application_id}")
            ]
        ]
        
        # Отправка данных в чат обратной связи
        await context.bot.send_message(
            chat_id=context.bot_data['config'].feedback_chat_id,
            text=messages.NEW_APPLICATION.format(
                title=vacancy.title,
                username=user.username or "Неизвестный пользователь",
                user_id=user.id,
                application_text=application_text
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        await update.message.reply_text(
            messages.APPLICATION_SENT,
            reply_markup=get_back_to_list_keyboard(),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        return ConversationHandler.END
    except Exception as e:
        log_message(user.id, user.username or "Unknown", "error", "Ошибка при обработке отклика", str(e))
        await update.message.reply_text(
            "Произошла ошибка при обработке отклика. Пожалуйста, попробуйте позже.",
            reply_markup=get_back_to_list_keyboard(),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        return ConversationHandler.END

async def back_to_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к списку вакансий"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    log_message(user.id, user.username or "Unknown", "back", "Вернулся к списку вакансий")
    
    db = Database()
    vacancies = db.get_active_vacancies()
    
    # Создаем клавиатуру с вакансиями
    keyboard = []
    row = []
    for i, vacancy in enumerate(vacancies, 1):
        row.append(
            InlineKeyboardButton(
                text=vacancy.title,
                callback_data=f"vacancy_{vacancy.id}"
            )
        )
        
        if i % 2 == 0 or i == len(vacancies):
            keyboard.append(row)
            row = []
    
    # Если пользователь админ, добавляем кнопку управления
    is_admin = db.is_admin(user.id)
    if is_admin:
        keyboard.append([
            InlineKeyboardButton(
                text="⚙️ Управление",
                callback_data="admin_panel"
            )
        ])
    
    if not vacancies:
        await query.message.edit_text(
            messages.NO_VACANCIES,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        return
    
    await query.message.edit_text(
        "📋 *Доступные вакансии:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик неизвестных сообщений"""
    user = update.effective_user
    log_message(user.id, user.username or "Unknown", "unknown", "Отправил неизвестное сообщение", f"Текст: {update.message.text[:50]}")
    
    db = Database()
    vacancies = db.get_active_vacancies()
    
    # Создаем клавиатуру с вакансиями
    keyboard = []
    row = []
    for i, vacancy in enumerate(vacancies, 1):
        row.append(
            InlineKeyboardButton(
                text=vacancy.title,
                callback_data=f"vacancy_{vacancy.id}"
            )
        )
        
        if i % 2 == 0 or i == len(vacancies):
            keyboard.append(row)
            row = []
    
    # Проверяем, является ли пользователь администратором
    is_admin = db.is_admin(user.id)
    
    # Для админа добавляем кнопку управления
    if is_admin:
        keyboard.append([
            InlineKeyboardButton(
                text="⚙️ Управление",
                callback_data="admin_panel"
            )
        ])
    
    await update.message.reply_text(
        messages.UNKNOWN_MESSAGE,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def show_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список доступных вакансий"""
    user = update.effective_user
    log_message(user.id, user.username or "Unknown", "view", "Открыл список вакансий")
    
    db = Database()
    vacancies = db.get_active_vacancies()
    
    # Создаем клавиатуру с вакансиями
    keyboard = []
    row = []
    for i, vacancy in enumerate(vacancies, 1):
        row.append(
            InlineKeyboardButton(
                text=vacancy.title,
                callback_data=f"vacancy_{vacancy.id}"
            )
        )
        
        if i % 2 == 0 or i == len(vacancies):
            keyboard.append(row)
            row = []
    
    # Если пользователь админ, добавляем кнопку управления
    is_admin = db.is_admin(user.id)
    if is_admin:
        keyboard.append([
            InlineKeyboardButton(
                text="⚙️ Управление",
                callback_data="admin_panel"
            )
        ])
    
    if not vacancies:
        await update.message.reply_text(
            messages.NO_VACANCIES,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        return
    
    await update.message.reply_text(
        "📋 *Доступные вакансии:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает информацию о боте"""
    user = update.effective_user
    log_message(user.id, user.username or "Unknown", "view", "Открыл информацию о боте")
    
    # Проверяем, является ли пользователь администратором
    db = Database()
    is_admin = db.is_admin(user.id)
    
    try:
        # Формируем текст сообщения
        text = messages.ABOUT_BOT
        if is_admin:
            admin_info = """

⚙️ *Панель администратора*
• Создание вакансий
• Управление откликами
• Модерация заявок"""
            text += admin_info
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    except Exception as e:
        log_message(user.id, user.username or "Unknown", "error", "Ошибка при показе информации о боте", str(e))
        # Отправляем текст без форматирования
        text_clean = text.replace('*', '').replace('`', '').replace('_', '')
        await update.message.reply_text(
            text_clean,
            disable_web_page_preview=True
        )

async def show_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список заявок пользователя"""
    user = update.effective_user
    log_message(user.id, user.username or "Unknown", "view", "Открыл свои заявки")
    
    db = Database()
    applications = db.get_user_applications(user.id)
    
    if not applications:
        await update.message.reply_text(
            messages.NO_APPLICATIONS,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        return
    
    # Форматируем список заявок
    applications_text = ""
    for title, description, applied_at, is_active, status, feedback in applications:
        date = datetime.fromisoformat(applied_at).strftime("%d.%m.%Y %H:%M")
        status_emoji, status_text = messages.APPLICATION_STATUS[status]
        feedback_text = f"\n💬 {feedback}" if feedback else ""
        
        applications_text += messages.APPLICATION_ITEM.format(
            title=title,
            date=date,
            status_emoji=status_emoji,
            status_text=status_text,
            feedback=feedback_text
        )
    
    await update.message.reply_text(
        messages.APPLICATIONS_LIST.format(applications=applications_text),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text
    
    if text == "📋 Вакансии":
        return await show_vacancies(update, context)
    elif text == "📝 Мои заявки":
        return await show_applications(update, context)
    elif text == "ℹ️ О боте":
        return await show_about(update, context)
    else:
        return await handle_unknown(update, context)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик неизвестных команд"""
    user = update.effective_user
    command = update.message.text
    log_message(user.id, user.username or "Unknown", "error", f"Неизвестная команда: {command}")
    
    await update.message.reply_text(
        "🤔 *Неизвестная команда*\n\n"
        "Используйте кнопки меню для навигации или следующие команды:\n"
        "• /start - Начать работу с ботом\n"
        "• /about - Информация о боте\n"
        "• /vacancies - Список вакансий\n"
        "• /applications - Ваши отклики",
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
