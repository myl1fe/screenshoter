import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import time
import logging
from pathlib import Path


class ScreenshotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ScreenshotScheduler"
    _svc_display_name_ = "Скриншотер - планировщик скриншотов"
    _svc_description_ = "Служба для автоматического создания скриншотов по расписанию"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_running = False
        self.scheduler = None

    def SvcStop(self):

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False
        if self.scheduler:
            self.scheduler.shutdown()

    def SvcDoRun(self):

        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        try:
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )
            self.main()
        except Exception as e:
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_ERROR_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, str(e)),
            )

    def setup_logging(self):

        try:

            log_dir = Path("C:\\ProgramData\\ScreenshotScheduler\\logs")
            log_dir.mkdir(parents=True, exist_ok=True)

            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[
                    logging.FileHandler(log_dir / "screenshot_service.log"),
                    logging.StreamHandler(sys.stdout),
                ],
            )
            self.logger = logging.getLogger(__name__)
        except Exception as e:

            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
            self.logger.error(f"Ошибка настройки логирования: {e}")

    def quick_setup(self):

        try:
            log_dir = Path("C:\\ScreenshotScheduler")
            log_dir.mkdir(exist_ok=True)
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[
                    logging.FileHandler(log_dir / "service_quick.log"),
                ],
            )
            self.logger = logging.getLogger(__name__)
            return True
        except:
            self.logging = None
            return True

    def load_config(self):

        try:
            config_path = Path("C:\\ProgramData\\ScreenshotScheduler\\config.json")
            if config_path.exists():
                import json

                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации: {e}")
            return {}

    def main(self):

        try:
            # Быстрая начальная настройка
            self.quick_setup()
            if self.logger:
                self.logger.info("Служба начинает запуск...")
            
            # Инициализируем планировщик в отдельном потоке
            self.initialize_scheduler_async()
            
            self.is_running = True
            if self.logger:
                self.logger.info("Служба запущена, ожидание остановки...")
            
            # Основной цикл - просто ожидаем остановки
            while self.is_running:
                win32event.WaitForSingleObject(self.hWaitStop, 5000)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ошибка в службе: {e}")
            # Пишем в системный журнал
            servicemanager.LogMsg(servicemanager.EVENTLOG_ERROR_TYPE,
                                servicemanager.PYS_SERVICE_STOPPED,
                                (self._svc_name_, str(e)))

    def initialize_scheduler_async(self):
        """Асинхронная инициализация планировщика"""
        try:
            if self.logger:
                self.logger.info("Начинаем асинхронную инициализацию планировщика...")
            
            # Импортируем здесь, чтобы не замедлять запуск
            from task_scheduler import ScreenshotScheduler
            self.scheduler = ScreenshotScheduler()
            
            # Быстрая загрузка конфигурации
            config = self.load_config_quick()
            
            # Загружаем задачи
            self.load_tasks_quick(config)
            
            # Запускаем планировщик
            if not self.scheduler.is_running():
                self.scheduler.start()
            
            if self.logger:
                self.logger.info("Планировщик успешно инициализирован")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ошибка инициализации планировщика: {e}")

    def initialize_scheduler_async(self):
        """Асинхронная инициализация планировщика"""
        try:
            if self.logger:
                self.logger.info("Начинаем асинхронную инициализацию планировщика...")
            
            # Импортируем здесь, чтобы не замедлять запуск
            from task_scheduler import ScreenshotScheduler
            self.scheduler = ScreenshotScheduler()
            
            # Быстрая загрузка конфигурации
            config = self.load_config_quick()
            
            # Загружаем задачи
            self.load_tasks_quick(config)
            
            # Запускаем планировщик
            if not self.scheduler.is_running():
                self.scheduler.start()
            
            if self.logger:
                self.logger.info("Планировщик успешно инициализирован")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ошибка инициализации планировщика: {e}")

    def load_tasks_from_config(self, config):

        try:
            tasks = config.get("tasks", [])
            self.logger.info(f"Найдено {len(tasks)} задач в конфигурации")

            for task in tasks:
                if task["type"] == "cron":
                    self.scheduler.add_cron_job(
                        task["id"],
                        task["hour"],
                        task["minute"],
                        task["days"],
                        task.get("args", []),
                    )
                elif task["type"] == "interval":
                    self.scheduler.add_interval_job(
                        task["id"], task["minutes"], task.get("args", [])
                    )

            self.logger.info("Задачи загружены в планировщик")

        except Exception as e:
            self.logger.error(f"Ошибка загрузки задач: {e}")

    def check_config_updated(self):

        try:
            config_path = Path("C:\\ProgramData\\ScreenshotScheduler\\config.json")
            if not config_path.exists():
                return False

            return False

        except Exception as e:
            self.logger.error(f"Ошибка проверки конфигурации: {e}")
            return False

    def reload_config(self):

        try:
            self.logger.info("Перезагрузка конфигурации...")
            config = self.load_config()

            self.scheduler.remove_all_jobs()

            self.load_tasks_from_config(config)

            self.logger.info("Конфигурация перезагружена")

        except Exception as e:
            self.logger.error(f"Ошибка перезагрузки конфигурации: {e}")


def main():
    if len(sys.argv) == 1:

        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ScreenshotService)
        servicemanager.StartServiceCtrlDispatcher()
    else:

        win32serviceutil.HandleCommandLine(ScreenshotService)


if __name__ == "__main__":
    main()
