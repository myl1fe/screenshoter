import sys
import time
import threading
import logging
import os
import traceback
from datetime import datetime

def setup_logging():
    """Настройка логирования для службы"""
    try:
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, 'screenshot_service.log')
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logging.info("Логирование настроено успешно")
    except Exception as e:
        error_log = os.path.join(log_dir, 'service_error.txt')
        with open(error_log, 'w', encoding='utf-8') as f:
            f.write(f"{datetime.now()} - Ошибка настройки логирования: {e}\n")

class ScreenshotService:
    def __init__(self):
        self.scheduler = None
        self.is_running = False
        self.logger = logging.getLogger()
        
    def start(self):
        """Запуск службы"""
        try:
            self.logger.info("Инициализация ScreenshotService...")
            
            # Исправляем импорт на правильное имя класса
            from task_scheduler import ScreenshotScheduler
            
            self.scheduler = ScreenshotScheduler()
            self.is_running = True
            
            # Запускаем планировщик
            self.scheduler.start()
            
            self.logger.info("ScreenshotService успешно запущен")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска службы: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def stop(self):
        """Остановка службы"""
        self.logger.info("Остановка ScreenshotService")
        self.is_running = False
        
        if self.scheduler:
            # Используем правильный метод shutdown
            self.scheduler.shutdown()
        self.logger.info("ScreenshotService остановлен")

def run_service():
    """Запуск службы"""
    setup_logging()
    logging.info("=== Запуск Screenshot Service ===")
    
    service = ScreenshotService()
    
    try:
        if service.start():
            logging.info("Служба запущена, вход в основной цикл...")
            # Основной цикл службы
            while service.is_running:
                time.sleep(5)
        else:
            logging.error("Не удалось запустить службу")
    except KeyboardInterrupt:
        logging.info("Получен сигнал прерывания")
    except Exception as e:
        logging.error(f"Неожиданная ошибка: {e}")
        logging.error(traceback.format_exc())
    finally:
        service.stop()
        logging.info("=== Служба завершена ===")

def main():
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1 and sys.argv[1] == "service":
        run_service()
    else:
        # Обычный GUI режим
        try:
            from gui_main import main as gui_main
            gui_main()
        except ImportError:
            # Если gui_main нет, пробуем gui
            from gui import main as gui_main
            gui_main()

if __name__ == "__main__":
    main()