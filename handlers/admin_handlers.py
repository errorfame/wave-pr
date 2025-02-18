from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import Database
from keyboards import get_admin_keyboard, get_admin_panel_keyboard, get_vacancies_keyboard, get_main_keyboard
from utils.decorators import admin_only
import messages
from utils.logger import log_message
from datetime import datetime

# Состояния для редактирования вакансий
EDIT_TITLE = 1
EDIT_DESCRIPTION = 2

# Состояния для добавления вакансии
AWAITING_TITLE = 1
AWAITING_DESCRIPTION = 2

def get_vacancy_edit_keyboard(vacancy_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Создает клавиатуру для редактирования вакансии"""
    status_emoji = "✅" if is_active else "❌"
    keyboard = [
        # Первая строка: название и описание
        [
            InlineKeyboardButton(
                text="📝 Изменить название",
                callback_data=f"edit_title_{vacancy_id}"
            ),
            InlineKeyboardButton(
                text="📄 Изменить описание",
                callback_data=f"edit_desc_{vacancy_id}"
            )
        ],
        # Вторая строка: статус и удаление
        [
            InlineKeyboardButton(
                text=f"Статус: {status_emoji}",
                callback_data=f"toggle_status_{vacancy_id}"
            ),
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=f"delete_vacancy_{vacancy_id}"
            )
        ],
        # Третья строка: кнопка назад
        [
            InlineKeyboardButton(
                text="↩️ Назад",
                callback_data="edit_vacancies"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

@admin_only
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start для администраторов"""
    user = update.effective_user
    log_message(user.id, user.username or "Unknown", "admin", "Открыл панель администратора")
    
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
    
    # Добавляем кнопку управления
    keyboard.append([
        InlineKeyboardButton(
            text="⚙️ Управление",
            callback_data="admin_panel"
        )
    ])
    
    # Формируем сообщение
    message_text = messages.ADMIN_START
    if vacancies:
        message_text += "\n\n📋 *Доступные вакансии:*"
    else:
        message_text += "\n\n❗️ *Нет активных вакансий*"
    
    # Отправляем сообщение с основной клавиатурой и инлайн-кнопками
    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    # Показываем основную клавиатуру отдельным действием
    await update.message.reply_text(
        "Используйте меню для навигации:",
        reply_markup=get_main_keyboard()
    )

@admin_only
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает панель управления администратора"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    log_message(user.id, user.username or "Unknown", "admin", "Открыл панель управления")
    
    await query.message.edit_text(
        messages.ADMIN_PANEL,
        reply_markup=get_admin_panel_keyboard(),
        parse_mode='Markdown'
    )

@admin_only
async def show_vacancies_for_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список вакансий для редактирования"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    log_message(user.id, user.username or "Unknown", "admin", "Открыл список вакансий для редактирования")
    
    db = Database()
    vacancies = db.get_all_vacancies()
    
    if not vacancies:
        await query.message.edit_text(
            "Нет доступных вакансий для редактирования.",
            reply_markup=get_admin_panel_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Создаем клавиатуру с вакансиями по две в строку
    keyboard = []
    row = []
    for i, vacancy in enumerate(vacancies, 1):
        status_emoji = "✅" if vacancy.is_active else "❌"
        row.append(
            InlineKeyboardButton(
                text=f"{status_emoji} {vacancy.title}",
                callback_data=f"edit_vacancy_{vacancy.id}"
            )
        )
        
        if i % 2 == 0 or i == len(vacancies):
            keyboard.append(row)
            row = []
    
    keyboard.append([
        InlineKeyboardButton(
            text="↩️ Назад",
            callback_data="admin_panel"
        )
    ])
    
    await query.message.edit_text(
        messages.EDIT_VACANCIES_LIST,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

@admin_only
async def edit_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню редактирования выбранной вакансии"""
    query = update.callback_query
    await query.answer()
    
    vacancy_id = int(query.data.split('_')[2])
    user = update.effective_user
    
    db = Database()
    vacancy = db.get_vacancy(vacancy_id)
    
    if not vacancy:
        await query.message.edit_text(
            "Вакансия не найдена.",
            reply_markup=get_admin_panel_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    log_message(user.id, user.username or "Unknown", "edit", "Начал редактирование вакансии", f"Вакансия: {vacancy.title}")
    
    status = "Активная ✅" if vacancy.is_active else "Неактивная ❌"
    await query.message.edit_text(
        messages.EDIT_VACANCY.format(
            title=vacancy.title,
            status=status,
            description=vacancy.description
        ),
        reply_markup=get_vacancy_edit_keyboard(vacancy_id, vacancy.is_active),
        parse_mode='Markdown'
    )

@admin_only
async def toggle_vacancy_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключает статус активности вакансии"""
    query = update.callback_query
    await query.answer()
    
    vacancy_id = int(query.data.split('_')[2])
    user = update.effective_user
    
    db = Database()
    vacancy = db.get_vacancy(vacancy_id)
    
    if not vacancy:
        await query.message.edit_text(
            "Вакансия не найдена.",
            parse_mode='Markdown'
        )
        return
    
    # Переключаем статус
    new_status = not vacancy.is_active
    db.update_vacancy(vacancy_id, is_active=new_status)
    
    status_text = "активировал" if new_status else "деактивировал"
    log_message(
        user.id,
        user.username or "Unknown",
        "edit",
        f"{status_text} вакансию",
        f"Вакансия: {vacancy.title}"
    )
    
    # Обновляем сообщение с новым статусом
    status = "Активная ✅" if new_status else "Неактивная ❌"
    await query.message.edit_text(
        messages.EDIT_VACANCY.format(
            title=vacancy.title,
            status=status,
            description=vacancy.description
        ),
        reply_markup=get_vacancy_edit_keyboard(vacancy_id, new_status),
        parse_mode='Markdown'
    )

@admin_only
async def delete_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет вакансию"""
    query = update.callback_query
    await query.answer()
    
    vacancy_id = int(query.data.split('_')[2])
    user = update.effective_user
    
    db = Database()
    vacancy = db.get_vacancy(vacancy_id)
    log_message(user.id, user.username or "Unknown", "deleted vacancy", f"Vacancy: {vacancy.title}")
    
    # Помечаем вакансию как неактивную вместо полного удаления
    db.update_vacancy(vacancy_id, is_active=False)
    
    await query.message.edit_text(
        messages.VACANCY_DELETED,
        reply_markup=get_admin_panel_keyboard(),
        parse_mode='Markdown'
    )

@admin_only
async def start_add_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса добавления вакансии"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    log_message(user.id, user.username or "Unknown", "admin", "Начал создание вакансии")
    
    await query.message.edit_text(
        "*Создание новой вакансии*\n\n"
        "Введите название вакансии.\n"
        "Например: Python Developer, Project Manager и т.д.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Отмена", callback_data="admin_panel")
        ]]),
        parse_mode='Markdown'
    )
    return AWAITING_TITLE

@admin_only
async def process_vacancy_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка названия вакансии"""
    user = update.effective_user
    title = update.message.text
    log_message(user.id, user.username or "Unknown", "edit", "Ввел название вакансии", f"Название: {title}")
    
    context.user_data['new_vacancy_title'] = title
    await update.message.reply_text(
        "*Отлично! Теперь введите описание вакансии.*\n\n"
        "Рекомендуемая структура:\n"
        "• Обязанности\n"
        "• Требования\n"
        "• Условия\n"
        "• Зарплата\n\n"
        "Используйте разделители и списки для лучшей читаемости.",
        parse_mode='Markdown'
    )
    return AWAITING_DESCRIPTION

@admin_only
async def process_vacancy_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка описания вакансии и сохранение вакансии"""
    user = update.effective_user
    title = context.user_data['new_vacancy_title']
    description = update.message.text
    
    db = Database()
    vacancy_id = db.add_vacancy(title, description)
    vacancy = db.get_vacancy(vacancy_id)
    
    log_message(user.id, user.username or "Unknown", "edit", "Создал новую вакансию", f"Название: {title}")
    
    await update.message.reply_text(
        f"✅ *Вакансия успешно создана!*\n\n"
        f"📋 *{vacancy.title}*\n\n"
        f"{vacancy.description}",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode='Markdown'
    )
    return ConversationHandler.END

@admin_only
async def start_edit_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс редактирования названия"""
    query = update.callback_query
    await query.answer()
    
    vacancy_id = int(query.data.split('_')[2])
    db = Database()
    vacancy = db.get_vacancy(vacancy_id)
    
    if not vacancy:
        await query.message.edit_text("Вакансия не найдена.", parse_mode='Markdown')
        return ConversationHandler.END
    
    context.user_data['editing_vacancy_id'] = vacancy_id
    
    await query.message.edit_text(
        messages.ENTER_NEW_TITLE.format(current_title=vacancy.title),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Отмена", callback_data=f"cancel_edit_{vacancy_id}")
        ]]),
        parse_mode='Markdown'
    )
    return EDIT_TITLE

@admin_only
async def start_edit_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс редактирования описания"""
    query = update.callback_query
    await query.answer()
    
    vacancy_id = int(query.data.split('_')[2])
    db = Database()
    vacancy = db.get_vacancy(vacancy_id)
    
    if not vacancy:
        await query.message.edit_text("Вакансия не найдена.", parse_mode='Markdown')
        return ConversationHandler.END
    
    context.user_data['editing_vacancy_id'] = vacancy_id
    
    await query.message.edit_text(
        messages.ENTER_NEW_DESCRIPTION.format(current_description=vacancy.description),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Отмена", callback_data=f"cancel_edit_{vacancy_id}")
        ]]),
        parse_mode='Markdown'
    )
    return EDIT_DESCRIPTION

@admin_only
async def process_edit_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает новое название вакансии"""
    vacancy_id = context.user_data.get('editing_vacancy_id')
    if not vacancy_id:
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте начать редактирование заново.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    new_title = update.message.text
    db = Database()
    db.update_vacancy(vacancy_id, title=new_title)
    vacancy = db.get_vacancy(vacancy_id)
    
    await update.message.reply_text(
        messages.VACANCY_UPDATED.format(
            title=vacancy.title,
            status="Активная ✅" if vacancy.is_active else "Неактивная ❌",
            description=vacancy.description
        ),
        reply_markup=get_vacancy_edit_keyboard(vacancy_id, vacancy.is_active),
        parse_mode='Markdown'
    )
    return ConversationHandler.END

@admin_only
async def process_edit_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает новое описание вакансии"""
    vacancy_id = context.user_data.get('editing_vacancy_id')
    if not vacancy_id:
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте начать редактирование заново.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    new_description = update.message.text
    db = Database()
    db.update_vacancy(vacancy_id, description=new_description)
    vacancy = db.get_vacancy(vacancy_id)
    
    await update.message.reply_text(
        messages.VACANCY_UPDATED.format(
            title=vacancy.title,
            status="Активная ✅" if vacancy.is_active else "Неактивная ❌",
            description=vacancy.description
        ),
        reply_markup=get_vacancy_edit_keyboard(vacancy_id, vacancy.is_active),
        parse_mode='Markdown'
    )
    return ConversationHandler.END

@admin_only
async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет редактирование"""
    query = update.callback_query
    await query.answer()
    
    vacancy_id = int(query.data.split('_')[2])
    db = Database()
    vacancy = db.get_vacancy(vacancy_id)
    
    await query.message.edit_text(
        messages.EDIT_VACANCY.format(
            title=vacancy.title,
            status="Активная ✅" if vacancy.is_active else "Неактивная ❌",
            description=vacancy.description
        ),
        reply_markup=get_vacancy_edit_keyboard(vacancy_id, vacancy.is_active),
        parse_mode='Markdown'
    )
    return ConversationHandler.END

@admin_only
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к главному меню администратора"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    log_message(user.id, user.username or "Unknown", "back", "Вернулся в главное меню")
    
    db = Database()
    vacancies = db.get_active_vacancies()
    
    # Создаем клавиатуру с вакансиями по две в строку
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
    
    # Добавляем кнопку управления
    keyboard.append([
        InlineKeyboardButton(
            text="⚙️ Управление",
            callback_data="admin_panel"
        )
    ])
    
    await query.message.edit_text(
        messages.BACK_TO_ADMIN_VACANCIES,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

@admin_only
async def process_application_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа на отклик (принятие/отклонение)"""
    query = update.callback_query
    await query.answer()
    
    # Получаем данные из callback_data: application_[accept/reject]_[id]
    parts = query.data.split('_')
    if len(parts) != 3:
        await query.message.edit_text("Ошибка в данных отклика.")
        return
    
    action = parts[1]
    application_id = int(parts[2])
    
    # Получаем информацию о модераторе
    moderator = update.effective_user
    moderator_name = f"@{moderator.username}" if moderator.username else f"ID: {moderator.id}"
    
    db = Database()
    application = db.get_application(application_id)
    if not application:
        await query.message.edit_text("Отклик не найден.")
        return
    
    vacancy = db.get_vacancy(application.vacancy_id)
    if not vacancy:
        await query.message.edit_text("Вакансия не найдена.")
        return
    
    # Обновляем статус отклика
    status = 'accepted' if action == 'accept' else 'rejected'
    feedback = None
    message_text = None
    
    if status == 'accepted':
        feedback = "Приглашаем вас на собеседование!"
        message_text = messages.APPLICATION_ACCEPTED.format(title=vacancy.title)
    else:
        feedback = "Спасибо за интерес к нашей компании."
        message_text = messages.APPLICATION_REJECTED.format(title=vacancy.title)
    
    db.update_application_status(application_id, status, feedback)
    
    # Отправляем уведомление пользователю
    try:
        await context.bot.send_message(
            chat_id=application.user_id,
            text=message_text,
            parse_mode='Markdown'
        )
        log_message(
            application.user_id,
            "System",
            "admin",
            f"Отклик {'принят' if status == 'accepted' else 'отклонен'}",
            f"Вакансия: {vacancy.title}"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления пользователю: {str(e)}")
    
    # Обновляем сообщение в админском чате
    status_emoji, status_text = messages.APPLICATION_STATUS[status]
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    await query.message.edit_text(
        messages.APPLICATION_RESPONSE.format(
            original_message=query.message.text,
            status_emoji=status_emoji,
            status_text=status_text,
            moderator=moderator_name,
            date=current_time
        ),
        parse_mode='Markdown'
    )
