import win32serviceutil
import win32service
import subprocess
import os
import sys
from pathlib import Path

class ServiceManager:
    def __init__(self):
        self.service_name = "ScreenshotScheduler"
        
    def install_service(self):
        
        try:
            
            script_path = os.path.abspath(__file__)
            
            
            win32serviceutil.InstallService(
                None,  
                self.service_name,
                "Screenshot Scheduler Service",
                startType=win32service.SERVICE_AUTO_START
            )
            
            print("Служба успешно установлена")
            return True
            
        except Exception as e:
            print(f"Ошибка установки службы: {e}")
            return False

    def uninstall_service(self):
        
        try:
            win32serviceutil.RemoveService(self.service_name)
            print("Служба успешно удалена")
            return True
        except Exception as e:
            print(f"Ошибка удаления службы: {e}")
            return False

    def start_service(self):
        """Запуск службы"""
        try:
            win32serviceutil.StartService(self.service_name)
            print("Служба запущена")
            return True
        except Exception as e:
            print(f"Ошибка запуска службы: {e}")
            return False

    def stop_service(self):
        
        try:
            win32serviceutil.StopService(self.service_name)
            print("Служба остановлена")
            return True
        except Exception as e:
            print(f"Ошибка остановки службы: {e}")
            return False

    def status_service(self):
        
        try:
            status = win32serviceutil.QueryServiceStatus(self.service_name)
            states = {
                1: "Остановлена",
                2: "Запускается", 
                3: "Останавливается",
                4: "Запущена",
                5: "Продолжается",
                6: "Приостановлена",
                7: "Пауза"
            }
            print(f"Статус службы: {states.get(status[1], 'Неизвестно')}")
            return True
        except Exception as e:
            print(f"Ошибка получения статуса: {e}")
            return False

def main():
    manager = ServiceManager()
    
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
            print("Использование: service_manager.py [install|uninstall|start|stop|status]")
    else:
        print("""
Утилита управления службой скриншотера

Команды:
  install   - Установить службу
  uninstall - Удалить службу  
  start     - Запустить службу
  stop      - Остановить службу
  status    - Показать статус службы

Пример: service_manager.py install
        """)

if __name__ == '__main__':
    main()