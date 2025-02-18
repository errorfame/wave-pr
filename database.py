import sqlite3
from typing import List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Vacancy:
    id: Optional[int]
    title: str
    description: str
    is_active: bool = True

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

    def _create_tables(self):
        """Создание необходимых таблиц"""
        with sqlite3.connect(self.db_path) as conn:
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
                    is_active BOOLEAN NOT NULL DEFAULT 1
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

    def add_vacancy(self, title: str, description: str) -> int:
        """Добавление новой вакансии"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO vacancies (title, description) VALUES (?, ?)",
                (title, description)
            )
            conn.commit()
            return cursor.lastrowid

    def get_vacancy(self, vacancy_id: int) -> Optional[Vacancy]:
        """Получение вакансии по ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, description, is_active FROM vacancies WHERE id = ?",
                (vacancy_id,)
            )
            result = cursor.fetchone()
            if result:
                return Vacancy(*result)
            return None

    def get_active_vacancies(self) -> List[Vacancy]:
        """Получение списка активных вакансий"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, description, is_active FROM vacancies WHERE is_active = 1"
            )
            return [Vacancy(*row) for row in cursor.fetchall()]

    def get_all_vacancies(self) -> List[Vacancy]:
        """Получение списка всех вакансий"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, description, is_active FROM vacancies"
            )
            return [Vacancy(*row) for row in cursor.fetchall()]

    def update_vacancy(self, vacancy_id: int, title: str = None, description: str = None, is_active: bool = None):
        """Обновление информации о вакансии"""
        updates = []
        values = []
        if title is not None:
            updates.append("title = ?")
            values.append(title)
        if description is not None:
            updates.append("description = ?")
            values.append(description)
        if is_active is not None:
            updates.append("is_active = ?")
            values.append(is_active)

        if not updates:
            return

        values.append(vacancy_id)
        query = f"UPDATE vacancies SET {', '.join(updates)} WHERE id = ?"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()

    def can_apply_to_vacancy(self, user_id: int, vacancy_id: int) -> bool:
        """Проверяет, может ли пользователь откликнуться на вакансию"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Проверяем последний отклик пользователя на эту вакансию
            cursor.execute("""
                SELECT applied_at 
                FROM applications 
                WHERE user_id = ? AND vacancy_id = ? 
                AND datetime(applied_at, '+24 hours') > datetime('now')
            """, (user_id, vacancy_id))
            
            result = cursor.fetchone()
            return result is None

    def add_application(self, user_id: int, vacancy_id: int) -> Optional[int]:
        """Добавляет отклик на вакансию и возвращает его ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO applications (user_id, vacancy_id) VALUES (?, ?)",
                    (user_id, vacancy_id)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None

    def add_admin(self, user_id: int, username: str = None) -> bool:
        """Добавляет нового администратора"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO admins (user_id, username) VALUES (?, ?)",
                    (user_id, username)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def remove_admin(self, user_id: int) -> bool:
        """Удаляет администратора"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_application(self, application_id: int) -> Optional[Application]:
        """Получает информацию об отклике по ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, vacancy_id, status, applied_at, feedback
                FROM applications WHERE id = ?
            """, (application_id,))
            result = cursor.fetchone()
            if result:
                return Application(*result)
            return None

    def update_application_status(self, application_id: int, status: str, feedback: str = None):
        """Обновляет статус отклика"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if feedback:
                cursor.execute(
                    "UPDATE applications SET status = ?, feedback = ? WHERE id = ?",
                    (status, feedback, application_id)
                )
            else:
                cursor.execute(
                    "UPDATE applications SET status = ? WHERE id = ?",
                    (status, application_id)
                )
            conn.commit()

    def get_user_applications(self, user_id: int) -> List[tuple]:
        """Получает список откликов пользователя с информацией о вакансиях"""
        with sqlite3.connect(self.db_path) as conn:
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
