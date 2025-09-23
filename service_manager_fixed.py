import win32serviceutil
import win32service
import subprocess
import os
import sys
import time
from pathlib import Path

class ServiceManagerFixed:
    def __init__(self):
        self.service_name = "ScreenshotScheduler"
        
    def install_service(self):
        """Установка службы с увеличенным таймаутом"""
        try:
            # Создаем простой конфиг
            self.create_simple_config()
            
            # Устанавливаем службу
            subprocess.run([
                'sc', 'create', self.service_name,
                'binPath=', f'"{sys.executable}" "{os.path.abspath("windows_service.py")}"',
                'start=', 'auto',
                'DisplayName=', '"Скриншотер - планировщик скриншотов"'
            ], check=True)
            
            # Увеличиваем таймаут службы
            subprocess.run([
                'sc', 'failure', self.service_name, 'reset=', '0', 'actions=', 'restart/0/restart/0/restart/0'
            ], check=True)
            
            # Устанавливаем увеличенный таймаут запуска
            subprocess.run([
                'sc', 'config', self.service_name, 'type=', 'own', 'start=', 'auto', 'error=', 'normal',
                'binPath=', f'"{sys.executable}" "{os.path.abspath("windows_service.py")}"'
            ], check=True)
            
            print("Служба успешно установлена с увеличенным таймаутом")
            return True
            
        except Exception as e:
            print(f"Ошибка установки службы: {e}")
            return False

    def create_simple_config(self):
        """Создает простой конфигурационный файл"""
        try:
            config_dir = Path("C:\\ScreenshotScheduler")
            config_dir.mkdir(exist_ok=True)
            
            config = {
                "tasks": [
                    {
                        "id": "simple_task",
                        "type": "interval", 
                        "minutes": 60,
                        "args": ["C:\\ScreenshotScheduler\\screenshots", False],
                        "enabled": True
                    }
                ]
            }
            
            config_path = config_dir / "config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(config, f, indent=2)
                
            print(f"Конфиг создан: {config_path}")
            return True
            
        except Exception as e:
            print(f"Ошибка создания конфига: {e}")
            return False

    def start_service(self):
        """Запуск службы с проверкой статуса"""
        try:
            print("Запуск службы...")
            subprocess.run(['sc', 'start', self.service_name], check=True)
            
            # Ждем и проверяем статус
            for i in range(30):  # Ждем до 30 секунд
                time.sleep(1)
                result = subprocess.run(['sc', 'query', self.service_name], 
                                      capture_output=True, text=True)
                if "RUNNING" in result.stdout:
                    print("Служба успешно запущена")
                    return True
                elif "STOPPED" in result.stdout:
                    print("Служба остановлена")
                    return False
                    
            print("Таймаут запуска службы")
            return False
            
        except Exception as e:
            print(f"Ошибка запуска службы: {e}")
            return False

    def stop_service(self):
        """Остановка службы"""
        try:
            subprocess.run(['sc', 'stop', self.service_name], check=True)
            print("Служба остановлена")
            return True
        except Exception as e:
            print(f"Ошибка остановки службы: {e}")
            return False

    def uninstall_service(self):
        """Удаление службы"""
        try:
            self.stop_service()
            time.sleep(2)
            subprocess.run(['sc', 'delete', self.service_name], check=True)
            print("Служба удалена")
            return True
        except Exception as e:
            print(f"Ошибка удаления службы: {e}")
            return False

    def status_service(self):
        """Статус службы"""
        try:
            result = subprocess.run(['sc', 'query', self.service_name], 
                                  capture_output=True, text=True)
            print(result.stdout)
            return True
        except Exception as e:
            print(f"Ошибка получения статуса: {e}")
            return False

def main():
    manager = ServiceManagerFixed()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "install":
            manager.install_service()
        elif command == "uninstall":
            manager.uninstall_service()
        elif command == "start":
            manager.start_service()
        elif command == "stop":
            manager.stop_service()
        elif command == "status":
            manager.status_service()
        else:
            print("Использование: service_manager_fixed.py [install|uninstall|start|stop|status]")
    else:
        print("""
Утилита управления службой скриншотера (исправленная)

Команды:
  install   - Установить службу с увеличенным таймаутом
  uninstall - Удалить службу  
  start     - Запустить службу с проверкой статуса
  stop      - Остановить службу
  status    - Показать статус службы

Пример: service_manager_fixed.py install
        """)

if __name__ == '__main__':
    main()