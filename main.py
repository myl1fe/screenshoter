# main.py (только для службы)

import time
import logging
import traceback
from task_scheduler import ScreenshotScheduler
import sys

def setup_logging():
    """Настройка логирования для службы"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'screenshot_service.log')),
            logging.StreamHandler()
        ]
    )

def run_service():
    """Запуск службы"""
    setup_logging()
    logging.info("=== Запуск Screenshot Service ===")
    
    scheduler = ScreenshotScheduler()
    scheduler.start()
    
    try:
        # Бесконечный цикл для службы
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        logging.info("Получен сигнал прерывания")
    except Exception as e:
        logging.error(f"Неожиданная ошибка: {e}")
        logging.error(traceback.format_exc())
    finally:
        scheduler.shutdown()
        logging.info("=== Служба завершена ===")

if __name__ == "__main__":
    # Если нужно, можно оставить возможность запуска с аргументом
    if len(sys.argv) > 1 and sys.argv[1] == "service":
        run_service()
    else:
        print("Для запуска службы используйте аргумент 'service'")
        print("Для запуска GUI используйте gui_main.py")