from database import Database

def init_database():
    db = Database()
    
    # Добавляем администратора
    db.add_admin(5535130491, "admin")  # Ваш ID из .env файла
    
    # Добавляем вакансию Backend-разработчика
    db.add_vacancy(
        "Backend-разработчик",
        """⚙️ *ВАКАНСИЯ: Backend-разработчик*

📋 *Требования:*
• Опыт работы 3-6 лет
• Опыт работы в JavaScript, Node JS
• Навыки профилирования и отладки Node JS проекта
• Опыт работы с реляционными СУБД (в т.ч. MySQL/MariaDB)

✨ *Будет плюсом:*
• Опыт работы с GTA 5 мультиплеер-платформами
• Опыт gamedev-разработки
• Опыт web-разработки, в т.ч. Vue.js
• Опыт работы с Sequelize, Redis или WebSockets

💼 *Обязанности:*
• Разработка и поддержка игровых систем на языке JavaScript (Node JS)
• Исправление существующих проблем в игровых системах
• Работа с другими разработчиками в команде для интеграции и улучшения систем

🎯 *Условия работы:*
• Конкурентная и стабильная оплата труда
• Бонусы за успехи на проекте
• Возможности для профессионального и карьерного роста
• Работа в команде опытных специалистов
• Культура открытости и взаимопомощи"""
    )
    
    # Добавляем вакансию Маппера
    db.add_vacancy(
        "Маппер",
        """🎨 *ВАКАНСИЯ: Маппер*

📋 *Требования:*
• Опыт работы в команде, где кандидат слышит и слушает, что от него просят
• Ответственность
• Психологическая устойчивость
• Опыт работы с двигателем игры GTA 5
• Общее понимание теории и стандартов игры
• Опыт работы в Blendere + Sollumz/ 3ds Max + GIMS
• Опыт использования софтов: Codewalker, OpenIV, VSC

✨ *Дополнительные навыки:*
• Substance Painter/Designer
• Marmoset
• Maya, Zbrush и другие

🎯 *Условия работы:*
• Свободный график работы
• Достойная и стабильная оплата труда
• Бонусы за успехи на проекте
• Возможности для профессионального роста
• Работа в команде опытных специалистов
• Культура открытости и взаимопомощи
• Возможность карьерного роста"""
    )

if __name__ == '__main__':
    init_database()
