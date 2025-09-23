import json
from pathlib import Path

def create_default_config():
    """Создает конфигурационный файл по умолчанию"""
    config = {
        "version": "1.0",
        "tasks": [
            {
                "id": "daily_screenshot_9am",
                "type": "cron",
                "hour": 9,
                "minute": 0,
                "days": [0, 1, 2, 3, 4, 5, 6],  # Все дни недели
                "args": ["screenshots", True],  # Папка и отправка email
                "enabled": True
            },
            {
                "id": "interval_screenshot_hourly", 
                "type": "interval",
                "minutes": 60,
                "args": ["screenshots", False],  # Без отправки email
                "enabled": True
            }
        ],
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "your_email@gmail.com",
            "password": "your_password",
            "from_addr": "your_email@gmail.com", 
            "to_addr": "recipient@gmail.com",
            "enabled": False
        }
    }
    
    # Создаем папку для конфигурации
    config_dir = Path("C:\\ProgramData\\ScreenshotScheduler")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Сохраняем конфигурацию
    config_path = config_dir / "config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"Конфигурационный файл создан: {config_path}")

if __name__ == '__main__':
    create_default_config()