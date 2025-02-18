# Wave Project - Work Bot 🎮

Telegram бот для управления вакансиями игрового проекта Wave Project - сервера GTA 5 в тематике Deathmatch.

## 🚀 Возможности

### Для кандидатов
- 📋 Просмотр актуальных вакансий проекта
- 💼 Моментальный отклик на интересные позиции
- 📊 Отслеживание статуса заявок
- 🔔 Уведомления об изменении статуса

### Для администраторов
- ⚙️ Создание и управление вакансиями
- 👥 Модерация откликов кандидатов
- 📝 Обработка заявок
- 📊 Просмотр статистики

## 🛠 Технологии
- Python 3.9+
- python-telegram-bot
- SQLite3
- Logging

## 📦 Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/wave-work-bot.git
cd wave-work-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` с вашими настройками:
```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_admin_telegram_id
FEEDBACK_CHAT_ID=your_feedback_chat_id
```

4. Инициализируйте базу данных:
```bash
python init_db.py
```

5. Запустите бота:
```bash
python main.py
```

## 🔧 Конфигурация

### Настройка администраторов
Для добавления нового администратора используйте команду в базе данных:
```sql
INSERT INTO admins (user_id, username) VALUES (user_telegram_id, 'username');
```

### Настройка чата обратной связи
1. Создайте канал или группу в Telegram
2. Добавьте бота в администраторы
3. Укажите ID чата в `.env` файле

## 📱 Использование

### Команды бота
- `/start` - Начало работы с ботом
- `/help` - Получить справку
- Используйте встроенную клавиатуру для навигации

### Управление вакансиями (для админов)
1. Откройте панель администратора
2. Используйте кнопку "⚙️ Управление"
3. Выберите нужное действие

## 🤝 Социальные сети
- Discord: discord.gg/waveproject
- Telegram: @wavegta5

## 📄 Лицензия
MIT License - подробности в файле [LICENSE](LICENSE)

## 👥 Авторы
- [@yourusername](https://github.com/yourusername) - Разработка
- Wave Project Team - Идея и поддержка
