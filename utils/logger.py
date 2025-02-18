import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from colorama import init, Fore, Style

# Инициализация colorama для Windows
init()

class ColoredFormatter(logging.Formatter):
    """Форматтер с цветным выводом"""
    
    COLORS = {
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
        'DEBUG': Fore.BLUE
    }
    
    ACTIONS = {
        'start': Fore.CYAN + '🚀 СТАРТ',
        'view': Fore.GREEN + '👀 ПРОСМОТР',
        'apply': Fore.BLUE + '📝 ОТКЛИК',
        'admin': Fore.YELLOW + '⚙️ АДМИН',
        'error': Fore.RED + '❌ ОШИБКА',
        'edit': Fore.MAGENTA + '✏️ ПРАВКА',
        'delete': Fore.RED + '🗑️ УДАЛЕНИЕ',
        'unknown': Fore.WHITE + '❓ НЕИЗВЕСТНО',
        'back': Fore.CYAN + '↩️ НАЗАД',
        'success': Fore.GREEN + '✅ УСПЕХ'
    }
    
    def format(self, record):
        if not record.msg.startswith('{'):
            return super().format(record)
            
        try:
            # Парсим сообщение
            parts = eval(record.msg)
            action_type = parts['type']
            username = parts['user']
            action = parts['action']
            details = parts.get('details', '')
            
            # Определяем цвет действия
            action_color = self.ACTIONS.get(action_type, self.ACTIONS['unknown'])
            
            # Форматируем время
            time_str = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
            
            # Собираем сообщение
            msg = (
                f"{Fore.WHITE}{time_str} | "
                f"{action_color} | "
                f"{Fore.CYAN}{username}{Fore.WHITE} | "
                f"{action}"
            )
            
            if details:
                msg += f" | {Fore.BLUE}{details}"
            
            # Сбрасываем цвет
            msg += Style.RESET_ALL
            
            return msg
        except:
            return super().format(record)

def setup_logger():
    """Настройка логгера"""
    # Создаем директорию для логов
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Настраиваем основной логгер
    logger = logging.getLogger('vacancy_bot')
    logger.setLevel(logging.INFO)

    # Форматтер для файла (без цветов)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Форматтер для консоли (с цветами)
    console_formatter = ColoredFormatter('%(message)s')

    # Хендлер для файла
    file_handler = RotatingFileHandler(
        f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log',
        maxBytes=5242880,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)

    # Хендлер для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # Добавляем хендлеры к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Отключаем логи от других модулей
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    logging.getLogger('telegram.ext.conversationhandler').setLevel(logging.ERROR)

    return logger

# Создаем и настраиваем логгер
logger = setup_logger()

def log_message(user_id: int, username: str, action_type: str, action: str, details: str = None):
    """
    Логирует действие пользователя
    
    :param user_id: ID пользователя
    :param username: Имя пользователя
    :param action_type: Тип действия (start, view, apply, admin, error, edit, delete, unknown)
    :param action: Описание действия
    :param details: Дополнительные детали
    """
    message = {
        'type': action_type,
        'user': f"{username} (ID: {user_id})",
        'action': action,
        'details': details
    }
    logger.info(str(message))
