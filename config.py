from environs import Env
from dataclasses import dataclass

@dataclass
class Config:
    """Конфигурация бота"""
    token: str
    feedback_chat_id: int

# Загрузка конфигурации из .env
def load_config() -> Config:
    env = Env()
    env.read_env()
    
    return Config(
        token=env.str('BOT_TOKEN'),
        feedback_chat_id=env.int('FEEDBACK_CHAT_ID')
    )
