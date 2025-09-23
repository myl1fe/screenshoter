import json
from pathlib import Path

def create_simple_config():
    """Создает упрощенный конфигурационный файл"""
    config = {
        "version": "1.0",
        "tasks": [
            {
                "id": "test_screenshot",
                "type": "interval",
                "minutes": 60,
                "args": ["C:\\ScreenshotScheduler\\screenshots", False],
                "enabled": True
            }
        ]
    }
    
    # Создаем папку для конфигурации
    config_dir = Path("C:\\ScreenshotScheduler")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаем папку для скриншотов
    screenshots_dir = config_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    
    # Сохраняем конфигурацию
    config_path = config_dir / "config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"Упрощенный конфигурационный файл создан: {config_path}")

if __name__ == '__main__':
    create_simple_config()