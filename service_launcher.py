# service_launcher.py
import sys
import os
import logging
import time
from pathlib import Path

# Настройка логирования для службы
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "service.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Запуск службы с существующей конфигурацией"""
    try:
        logging.info("=== Запуск Screenshot Service ===")
        
        # Создаем файл блокировки для индикации работы службы
        lock_file = Path("service.lock")
        lock_file.touch()
        
        # Проверяем существование конфига
        config_path = Path("config.json")
        if not config_path.exists():
            logging.info("Конфиг не найден, создаем простой конфиг...")
            # Запускаем создание простого конфига
            import create_simple_config
            # или import create_config - в зависимости от того, что у вас
        
        logging.info(f"Конфиг загружен: {config_path}")
        
        # Импортируем и запускаем службу
        from main import run_service
        run_service()
        
    except Exception as e:
        logging.error(f"Ошибка запуска службы: {e}")
        import traceback
        logging.error(traceback.format_exc())
    finally:
        # Удаляем файл блокировки при остановке
        if 'lock_file' in locals() and lock_file.exists():
            lock_file.unlink()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "service":
        main()
    else:
        print("Использование: python service_launcher.py service")