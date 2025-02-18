from typing import Dict, Tuple
from time import time
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class UserState:
    """Состояние пользователя для защиты от спама"""
    message_count: int = 0
    last_message_time: float = 0
    is_blocked: bool = False
    block_until: datetime = datetime.min

class RateLimiter:
    def __init__(
        self,
        messages_per_minute: int = 20,
        max_similar_messages: int = 5,
        block_duration_minutes: int = 5
    ):
        self.messages_per_minute = messages_per_minute
        self.max_similar_messages = max_similar_messages
        self.block_duration = timedelta(minutes=block_duration_minutes)
        self.user_states: Dict[int, UserState] = {}
        self.user_last_messages: Dict[int, Tuple[str, int]] = {}  # (message, count)
        
    def can_send_message(self, user_id: int, message_text: str = "") -> Tuple[bool, str]:
        """Проверяет, может ли пользователь отправить сообщение"""
        current_time = time()
        
        # Получаем или создаем состояние пользователя
        user_state = self.user_states.get(user_id, UserState())
        
        # Проверяем блокировку
        if user_state.is_blocked:
            if datetime.now() < user_state.block_until:
                remaining = (user_state.block_until - datetime.now()).seconds
                return False, f"Вы временно заблокированы. Осталось {remaining} секунд."
            else:
                user_state.is_blocked = False
        
        # Проверяем частоту сообщений
        if current_time - user_state.last_message_time < 60:  # в течение минуты
            user_state.message_count += 1
            if user_state.message_count > self.messages_per_minute:
                user_state.is_blocked = True
                user_state.block_until = datetime.now() + self.block_duration
                self.user_states[user_id] = user_state
                return False, f"Слишком много сообщений. Вы заблокированы на {self.block_duration.seconds // 60} минут."
        else:
            # Сбрасываем счетчик после минуты
            user_state.message_count = 1
        
        # Проверяем повторяющиеся сообщения
        last_message, count = self.user_last_messages.get(user_id, ("", 0))
        if message_text == last_message:
            count += 1
            if count > self.max_similar_messages:
                user_state.is_blocked = True
                user_state.block_until = datetime.now() + self.block_duration
                self.user_states[user_id] = user_state
                return False, f"Обнаружен спам повторяющимися сообщениями. Блокировка на {self.block_duration.seconds // 60} минут."
            self.user_last_messages[user_id] = (message_text, count)
        else:
            self.user_last_messages[user_id] = (message_text, 1)
        
        # Обновляем состояние пользователя
        user_state.last_message_time = current_time
        self.user_states[user_id] = user_state
        
        return True, ""

    def reset_user(self, user_id: int):
        """Сбрасывает все ограничения для пользователя"""
        if user_id in self.user_states:
            del self.user_states[user_id]
        if user_id in self.user_last_messages:
            del self.user_last_messages[user_id]
