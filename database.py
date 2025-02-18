import sqlite3
from typing import List, Optional, Tuple
from dataclasses import dataclass
import re
from contextlib import contextmanager

@dataclass
class Vacancy:
    id: Optional[int]
    title: str
    description: str
    is_active: bool = True
    image_id: Optional[str] = None

@dataclass
class Application:
    id: Optional[int]
    user_id: int
    vacancy_id: int
    status: str  # pending, accepted, rejected
    applied_at: str
    feedback: Optional[str] = None

class Database:
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
        self._create_tables()
    
    @contextmanager
    def get_connection(self):
        """Безопасное получение соединения с базой данных"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def _sanitize_input(self, text: str) -> str:
        """Очищает входные данные от потенциально опасных символов"""
        if not isinstance(text, str):
            return ""
        # Удаляем специальные символы и ограничиваем длину
        text = re.sub(r'[^\w\s\-.,!?@()\'\"]+', '', text)
        return text[:1000]  # Ограничиваем длину текста
    
    def _create_tables(self):
        """Создание необходимых таблиц"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Таблица администраторов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Таблица вакансий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vacancies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    image_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Таблица откликов на вакансии
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    vacancy_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    feedback TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vacancy_id) REFERENCES vacancies (id),
                    UNIQUE(user_id, vacancy_id)
                )
            """)
            conn.commit()

    def add_admin(self, user_id: int, username: str) -> bool:
        """Добавляет администратора"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO admins (user_id, username) VALUES (?, ?)",
                    (user_id, self._sanitize_input(username))
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def add_vacancy(self, title: str, description: str, image_id: str = None) -> Optional[int]:
        """Добавляет вакансию"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO vacancies (title, description, image_id) VALUES (?, ?, ?)",
                    (title, description, image_id)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error:
            return None

    def update_vacancy(self, vacancy_id: int, title: str = None, description: str = None, is_active: bool = None, image_id: str = None) -> bool:
        """Обновляет информацию о вакансии"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Собираем параметры для обновления
                updates = []
                values = []
                
                if title is not None:
                    updates.append("title = ?")
                    values.append(self._sanitize_input(title))
                
                if description is not None:
                    updates.append("description = ?")
                    values.append(self._sanitize_input(description))
                
                if is_active is not None:
                    updates.append("is_active = ?")
                    values.append(is_active)
                
                if image_id is not None:
                    updates.append("image_id = ?")
                    values.append(image_id)
                
                if not updates:
                    return False
                
                # Добавляем ID вакансии в конец значений
                values.append(vacancy_id)
                
                # Формируем и выполняем запрос
                query = f"UPDATE vacancies SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, values)
                conn.commit()
                
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def get_vacancy(self, vacancy_id: int) -> Optional[Vacancy]:
        """Получает информацию о вакансии"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, title, description, is_active, image_id FROM vacancies WHERE id = ?",
                    (vacancy_id,)
                )
                result = cursor.fetchone()
                if result:
                    # Возвращаем текст как есть, без изменений
                    return Vacancy(*result)
                return None
        except sqlite3.Error:
            return None

    def get_active_vacancies(self) -> List[Vacancy]:
        """Получает список активных вакансий"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, title, description, is_active, image_id FROM vacancies WHERE is_active = 1"
                )
                return [Vacancy(*row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_all_vacancies(self) -> List[Vacancy]:
        """Получает список всех вакансий для администратора"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, description, is_active, image_id 
                    FROM vacancies 
                    ORDER BY created_at DESC
                """)
                return [Vacancy(*row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def toggle_vacancy_status(self, vacancy_id: int) -> bool:
        """Переключает статус активности вакансии"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE vacancies SET is_active = NOT is_active WHERE id = ?",
                    (vacancy_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def update_vacancy_status(self, vacancy_id: int, is_active: bool) -> bool:
        """Обновляет статус вакансии"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE vacancies SET is_active = ? WHERE id = ?",
                    (is_active, vacancy_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def delete_vacancy(self, vacancy_id: int) -> bool:
        """Удаляет вакансию"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Сначала удаляем все отклики на эту вакансию
                cursor.execute("DELETE FROM applications WHERE vacancy_id = ?", (vacancy_id,))
                # Затем удаляем саму вакансию
                cursor.execute("DELETE FROM vacancies WHERE id = ?", (vacancy_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def add_application(self, user_id: int, vacancy_id: int) -> Optional[int]:
        """Добавляет отклик на вакансию"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO applications (user_id, vacancy_id) VALUES (?, ?)",
                    (user_id, vacancy_id)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def update_application_status(self, application_id: int, status: str, feedback: str = None) -> bool:
        """Обновляет статус отклика"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if feedback:
                    cursor.execute(
                        "UPDATE applications SET status = ?, feedback = ? WHERE id = ?",
                        (status, self._sanitize_input(feedback), application_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE applications SET status = ? WHERE id = ?",
                        (status, application_id)
                    )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def get_application(self, application_id: int) -> Optional[Application]:
        """Получает информацию об отклике"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, user_id, vacancy_id, status, applied_at, feedback
                    FROM applications WHERE id = ?
                """, (application_id,))
                result = cursor.fetchone()
                return Application(*result) if result else None
        except sqlite3.Error:
            return None

    def get_user_applications(self, user_id: int) -> List[tuple]:
        """Получает список откликов пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        v.title,
                        v.description,
                        a.applied_at,
                        v.is_active,
                        a.status,
                        a.feedback
                    FROM applications a
                    JOIN vacancies v ON v.id = a.vacancy_id
                    WHERE a.user_id = ?
                    ORDER BY a.applied_at DESC
                """, (user_id,))
                return cursor.fetchall()
        except sqlite3.Error:
            return []

    def can_apply_to_vacancy(self, user_id: int, vacancy_id: int) -> bool:
        """Проверяет, может ли пользователь откликнуться на вакансию"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Проверяем, не отправлял ли пользователь отклик в последние 24 часа
                cursor.execute("""
                    SELECT applied_at 
                    FROM applications 
                    WHERE user_id = ? AND vacancy_id = ? 
                    AND datetime(applied_at, '+24 hours') > datetime('now')
                """, (user_id, vacancy_id))
                
                result = cursor.fetchone()
                
                if result:
                    return False  # Уже отправлял отклик недавно
                
                # Проверяем, активна ли вакансия
                cursor.execute(
                    "SELECT is_active FROM vacancies WHERE id = ?",
                    (vacancy_id,)
                )
                vacancy = cursor.fetchone()
                
                return vacancy is not None and vacancy[0]
        except sqlite3.Error:
            return False

    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False
