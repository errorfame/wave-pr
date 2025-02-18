from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import List
from database import Vacancy

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Создает основную клавиатуру"""
    keyboard = [
        [KeyboardButton("📋 Вакансии"), KeyboardButton("📝 Мои заявки")],
        [KeyboardButton("ℹ️ О боте")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_vacancies_keyboard(vacancies: List[Vacancy]) -> InlineKeyboardMarkup:
    """Создает клавиатуру со списком вакансий"""
    keyboard = []
    for vacancy in vacancies:
        keyboard.append([
            InlineKeyboardButton(
                text=vacancy.title,
                callback_data=f"vacancy_{vacancy.id}"
            )
        ])
    
    if not keyboard:  # Если нет вакансий, добавляем информационную кнопку
        keyboard.append([
            InlineKeyboardButton(
                text="Нет доступных вакансий",
                callback_data="no_vacancies"
            )
        ])
    
    return InlineKeyboardMarkup(keyboard)

def get_vacancy_actions_keyboard(vacancy_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру действий для конкретной вакансии"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="Откликнуться",
                callback_data=f"apply_{vacancy_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="↩️ К списку вакансий",
                callback_data="back_to_vacancies"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_list_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для возврата к списку вакансий"""
    keyboard = [[
        InlineKeyboardButton(
            "« Назад к списку",
            callback_data="back_to_vacancies"
        )
    ]]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру администратора"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="⚙️ Управление",
                callback_data="admin_panel"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура панели администратора"""
    keyboard = [
        [
            InlineKeyboardButton(
                "📝 Добавить вакансию",
                callback_data="add_vacancy"
            )
        ],
        [
            InlineKeyboardButton(
                "📋 Редактировать вакансии",
                callback_data="edit_vacancies"
            )
        ],
        [
            InlineKeyboardButton(
                "« Вернуться в меню",
                callback_data="back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_edit_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для возврата к списку вакансий"""
    keyboard = [[
        InlineKeyboardButton(
            "« Назад к списку вакансий",
            callback_data="edit_vacancies"
        )
    ]]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой возврата в главное меню"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="↩️ В главное меню",
                callback_data="back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_edit_vacancy_keyboard(vacancy_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для редактирования вакансии"""
    keyboard = [
        [
            InlineKeyboardButton(
                "✏️ Изменить название",
                callback_data=f"edit_title_{vacancy_id}"
            ),
            InlineKeyboardButton(
                "📝 Изменить описание",
                callback_data=f"edit_description_{vacancy_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_edit_keyboard(vacancy_id: int):
    """Клавиатура для отмены редактирования"""
    keyboard = [[
        InlineKeyboardButton(
            "❌ Отменить",
            callback_data=f"cancel_edit_{vacancy_id}"
        )
    ]]
    return InlineKeyboardMarkup(keyboard)
