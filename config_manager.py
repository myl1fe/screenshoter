import json
import logging
from pathlib import Path
from datetime import datetime

class ConfigManager:
    def __init__(self, config_path="app.config.json"):
        self.config_path = Path(config_path)
        self.config = None
        self.load_config()
    
    def load_config(self):
        """Загрузка конфигурации из файла"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logging.info(f"Конфиг загружен из {self.config_path}")
            else:
                self.create_default_config()
                logging.info("Создан конфиг по умолчанию")
        except Exception as e:
            logging.error(f"Ошибка загрузки конфига: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Создание конфигурации по умолчанию"""
        self.config = {
            "version": "1.0",
            "last_modified": datetime.now().isoformat(),
            "service_settings": {
                "enabled": True,
                "check_interval": 30
            },
            "screenshot_settings": {
                "default_save_dir": "screenshots",
                "format": "png",
                "quality": 85
            },
            "email_settings": {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_addr": "",
                "to_addr": ""
            },
            "tasks": [
                {
                    "id": "test_interval",
                    "type": "interval",
                    "minutes": 5,
                    "args": ["screenshots", False],
                    "enabled": True
                }
            ]
        }
        self.save_config()
    
    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            self.config["last_modified"] = datetime.now().isoformat()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logging.info(f"Конфиг сохранен в {self.config_path}")
            return True
        except Exception as e:
            logging.error(f"Ошибка сохранения конфига: {e}")
            return False
    
    # Методы для работы с задачами
    def get_tasks(self):
        """Получение списка задач"""
        return self.config.get("tasks", [])
    
    def add_task(self, task_data):
        """Добавление новой задачи"""
        tasks = self.config.get("tasks", [])
        tasks.append(task_data)
        self.config["tasks"] = tasks
        return self.save_config()
    
    def update_task(self, task_id, task_data):
        """Обновление существующей задачи"""
        tasks = self.config.get("tasks", [])
        for i, task in enumerate(tasks):
            if task.get("id") == task_id:
                tasks[i] = task_data
                self.config["tasks"] = tasks
                return self.save_config()
        return False
    
    def delete_task(self, task_id):
        """Удаление задачи"""
        tasks = self.config.get("tasks", [])
        tasks = [task for task in tasks if task.get("id") != task_id]
        self.config["tasks"] = tasks
        return self.save_config()
    
    def get_task(self, task_id):
        """Получение задачи по ID"""
        tasks = self.config.get("tasks", [])
        for task in tasks:
            if task.get("id") == task_id:
                return task
        return None
    
    # Методы для работы с настройками
    def get_email_settings(self):
        """Получение настроек email"""
        return self.config.get("email_settings", {})
    
    def update_email_settings(self, settings):
        """Обновление настроек email"""
        self.config["email_settings"] = settings
        return self.save_config()
    
    def get_screenshot_settings(self):
        """Получение настроек скриншотов"""
        return self.config.get("screenshot_settings", {})
    
    def update_screenshot_settings(self, settings):
        """Обновление настроек скриншотов"""
        self.config["screenshot_settings"] = settings
        return self.save_config()
    
    def get_service_settings(self):
        """Получение настроек службы"""
        return self.config.get("service_settings", {})
    
    def update_service_settings(self, settings):
        """Обновление настроек службы"""
        self.config["service_settings"] = settings
        return self.save_config()
    
    def is_service_running(self):
        """Проверка, запущена ли служба (через файл блокировки)"""
        try:
            lock_file = Path("service.lock")
            if lock_file.exists():
                import time
                lock_time = lock_file.stat().st_mtime
                return (time.time() - lock_time) < 60
            return False
        except:
            return False

# Функция для быстрого создания конфига
def create_config():
    """Создает конфигурационный файл (аналог старого create_config.py)"""
    cm = ConfigManager()
    print(f"✅ Конфигурационный файл создан: {cm.config_path}")
    print(f"📋 Задач: {len(cm.get_tasks())}")
    return cm

def create_simple_config():
    """Создает упрощенный конфиг (аналог старого create_simple_config.py)"""
    cm = ConfigManager("simple.config.json")
    # Упрощаем конфиг
    cm.config = {
        "version": "1.0",
        "tasks": [
            {
                "id": "simple_screenshot",
                "type": "interval",
                "minutes": 10,
                "args": ["screenshots", False],
                "enabled": True
            }
        ]
    }
    cm.save_config()
    print(f"✅ Упрощенный конфиг создан: {cm.config_path}")
    return cm

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        create_simple_config()
    else:
        create_config()