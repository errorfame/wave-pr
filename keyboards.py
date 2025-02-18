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
    """Создает клавиатуру с кнопкой возврата к списку вакансий"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="↩️ К списку вакансий",
                callback_data="back_to_vacancies"
            )
        ]
    ]
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
    """Создает клавиатуру панели управления"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="➕ Добавить вакансию",
                callback_data="add_vacancy"
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 Редактировать вакансии",
                callback_data="edit_vacancies"
            )
        ],
        [
            InlineKeyboardButton(
                text="↩️ Назад",
                callback_data="back_to_main"
            )
        ]
    ]
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
