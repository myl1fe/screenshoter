from screenshoter import take_screenshots_mss
from email_sender import EmailSender

from datetime import datetime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import ConflictingIdError
from apscheduler.jobstores.memory import MemoryJobStore

import logging 
import atexit
import os
from pathlib import Path
import sys
import psutil

from config_manager import ConfigManager
import time
import threading
import json

from screenshoter import take_screenshots_mss

# Проверка что это функция
print(f"take_screenshots_mss type: {type(take_screenshots_mss)}")
print(f"take_screenshots_mss callable: {callable(take_screenshots_mss)}")

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

email_config = {
    'enabled': False,
    'smtp_server': None,
    'smtp_port': None,
    'username': None,
    'password': None,
    'from_addr': None,
    'to_addr': None
}



class ScreenshotScheduler:
    def __init__(self, db_path='scheduler.db'):
        # Инициализация конфиг менеджера
        self.config_manager = ConfigManager("app.config.json")
        
        self.is_service = self.check_service_mode()
        self.setup_logging()
        
        # Инициализация планировщика
        jobstores = {
            'default': MemoryJobStore()
        }        
        self.scheduler = BackgroundScheduler(jobstores=jobstores)
        self.jobs = {}   
 
        # Регистрация завершения и инициализация email
        atexit.register(self.shutdown)
        self.email_sender = EmailSender()
        
        # Загрузка задач из конфига
        self.load_jobs_from_config()
        
        # Мониторинг изменений конфига (только для службы)
        self.config_monitor_thread = None
        self.is_running = False

    
    def check_service_mode(self):        
        try:
            # Проверяем аргументы командной строки
            if len(sys.argv) > 1 and sys.argv[1] == "service":
                return True
                
            # Проверяем, запущен ли как служба Windows
            if 'win32service' in sys.modules:
                return True
                
            # Дополнительная проверка для NSSM
            
            current_process = psutil.Process()
            parent_name = current_process.parent().name().lower()
            if 'nssm' in parent_name or 'services.exe' in parent_name:
                return True
            
            return False
        except:
            return False
    def setup_service_logging(self):
       
        log_dir = Path("C:\\ProgramData\\ScreenshotScheduler\\logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "scheduler.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
    def setup_app_logging(self):
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    def take_screenshot_handler(self, save_dir='screenshots', send_email=False):
            try:
                logging.info(f"Выполнение задачи: save_dir={save_dir}, send_email={send_email}")
                saved_screens = take_screenshots_mss(save_dir)  # ← Убедитесь, что это функция
                if saved_screens:
                    logging.info(f"Скриншоты созданы: {saved_screens}")
                    
                    if send_email:
                        subject = f"Скриншоты от {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        body = "Автоматически отправленные скриншоты"
                        self.email_sender.send_email(subject, body, saved_screens)
                    
                    return saved_screens
            except Exception as e:
                logging.error(f"Ошибка в задаче: {e}")
                return None
    
    def setup_logging(self):
        """Настройка логирования"""
        log_level = logging.INFO
        if self.is_service:
            log_dir = Path("logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_dir / "scheduler.log"),
                    logging.StreamHandler(sys.stdout)
                ]
            )
        else:
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
    
    def load_jobs_from_config(self):        
        try:
            
            for job_id in list(self.jobs.keys()):
                self.remove_existing_job(job_id)
            
            # Загружаем задачи из конфига
            tasks = self.config_manager.get_tasks()
            email_settings = self.config_manager.get_email_settings()
            
            # Настраиваем email
            self.configure_email(**email_settings)
            
            # Добавляем задачи в планировщик
            for task in tasks:
                if task.get('enabled', True):
                    self.add_job_from_config(task)
            
            logging.info(f"Загружено {len(tasks)} задач из конфига")
            
        except Exception as e:
            logging.error(f"Ошибка загрузки задач из конфига: {e}")

    
    def add_job_from_config(self, task):
        """Добавление задачи из конфигурации"""
        try:
            task_id = task['id']
            task_type = task['type']
            args = task.get('args', ['screenshots', False])
            
            if task_type == 'interval':
                minutes = task.get('minutes', 5)
                self.add_interval_job(task_id, minutes, args)
            elif task_type == 'cron':
                hour = task.get('hour', 0)
                minute = task.get('minute', 0)
                days = task.get('days', [1, 2, 3, 4, 5])
                self.add_cron_job(task_id, hour, minute, days, args)
                
        except Exception as e:
            logging.error(f"Ошибка добавления задачи {task.get('id', 'unknown')}: {e}")
    
    def start_config_monitor(self):
        if self.is_service:
            self.is_running = True
            self.config_monitor_thread = threading.Thread(target=self._monitor_config_changes)
            self.config_monitor_thread.daemon = True
            self.config_monitor_thread.start()
    
    def _monitor_config_changes(self):
        last_modified = self.config_manager.config_path.stat().st_mtime
        
        while self.is_running:
            try:
                current_modified = self.config_manager.config_path.stat().st_mtime
                if current_modified > last_modified:
                    logging.info("Обнаружены изменения в конфиге, перезагружаем задачи...")
                    self.load_jobs_from_config()
                    last_modified = current_modified
                
                time.sleep(10)  # Проверяем каждые 10 секунд
            except Exception as e:
                logging.error(f"Ошибка мониторинга конфига: {e}")
                time.sleep(30)
    
    
    def shutdown(self):
        
        self.is_running = False
        if self.scheduler.running:
            self.scheduler.shutdown()
        logging.info("Планировщик остановлен")
    
    def remove_all_jobs(self):
        try:
            self.scheduler.remove_all_jobs()
            self.jobs.clear()
            logging.info("Все задачи удалены")
            return True
        except Exception as e:
            logging.error(f"Ошибка при удалении всех задач: {e}")
            return False
        
        
                
    def check_job_conflict(self, job_id):
        return job_id in self.jobs
        
    def get_job_info(self, job_id):

        if job_id in self.jobs:
            job = self.jobs[job_id]
            trigger = job.trigger

            if hasattr(trigger, 'fields'):
                return f'Задание по типу {type(trigger).__name__}, в следующий раз будет запущена: {job.next_run_time}'
            return f'Тип задачи {type(trigger).__name__}'
        return f'Таких задач нет.'



    def get_jobs(self):
        return self.scheduler.get_jobs()
    
    def start(self):
        
        self.is_running = False
        if self.scheduler.running:
            self.scheduler.shutdown()
        logging.info("Планировщик остановлен")
    
    def add_cron_job(self, job_id, hour, minute, days_of_week, args=None):
        try:
            if self.check_job_conflict(job_id):
                self.remove_existing_job(job_id)
            
            days_cron = ','.join(map(str, days_of_week))

            trigger = CronTrigger(
                day_of_week=days_cron,
                hour=hour,
                minute=minute,
                timezone='Europe/Moscow'
            )

            logging.info(f"take_screenshot_handler: {self.take_screenshot_handler}, type: {type(self.take_screenshot_handler)}")
            job = self.scheduler.add_job(
                self.take_screenshot_handler, 
                trigger,
                args=args or [],
                id=job_id
            )

            self.jobs[job_id] = job
            logging.info(f'task {job_id} added for {hour} and {minute} by {days_of_week}')
            return job_id
        
        except Exception as e:
            logging.error(f'Не удалось добавить задачу {job_id}: {e}')
            return None

    def add_interval_job(self, job_id, minutes, args=None):
        try:
            logging.info(f"Добавление интервальной задачи: {job_id}, интервал: {minutes} минут")
            if self.check_job_conflict(job_id):
                self.remove_existing_job(job_id)
            
            trigger = IntervalTrigger(minutes=minutes)
            logging.info(f"take_screenshot_handler: {self.take_screenshot_handler}, type: {type(self.take_screenshot_handler)}")

            job = self.scheduler.add_job(
                                        self.take_screenshot_handler,  
                                        trigger,
                                        args=args or [],
                                        id=job_id
                                    )

            self.jobs[job_id] = job
            logging.info(f'Интервальная задача {job_id} добавлена: каждые {minutes} минут')

            if job in self.scheduler.get_jobs():
                logging.info(f"Задача {job_id} успешно добавлена в планировщик")
            else:
                logging.warning(f"Задача {job_id} не найдена в планировщике")


            return job_id
        except ConflictingIdError:
            logging.error(f'Конфликт ID задачи: {job_id}')
            return None
        except Exception as e:
            logging.error(f'Не удалось добавить интервальную задачу {job_id}: {e}')
            return None
    
    
    def remove_existing_job(self, job_id):
    
        try:
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                logging.info(f'Задача {job_id} удалена')
                return True
            return False
        except Exception as e:
            logging.error(f'Ошибка при удалении задачи {job_id}: {e}')
            return False

    def get_detailed_job_info(self, job_id):
        if job_id in self.jobs:
            job = self.jobs[job_id]
            info = {
                'id': job.id,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger),
                'args': job.args
                }
            return info
        return None

    def configure_email(self, smtp_server, smtp_port, username, password, from_addr, to_addr, enabled):
        if not hasattr(self, 'email_sender'):
            from email_sender import EmailSender
            self.email_sender = EmailSender()
            
        self.email_sender.configure(smtp_server, smtp_port, username, password, from_addr, to_addr, enabled)

    def add_task_to_scheduler(self, task_data):
        """Добавление задачи в планировщик (вызывается при загрузке из конфига)"""
        try:
            task_id = task_data['id']
            task_type = task_data['type']
            args = task_data.get('args', ['screenshots', False])
            
            if task_type == 'interval':
                minutes = task_data.get('minutes', 5)
                return self.add_interval_job(task_id, minutes, args)
            elif task_type == 'cron':
                hour = task_data.get('hour', 0)
                minute = task_data.get('minute', 0)
                days = task_data.get('days', [1, 2, 3, 4, 5])
                return self.add_cron_job(task_id, hour, minute, days, args)
            return None
                
        except Exception as e:
            logging.error(f"Ошибка добавления задачи {task_data.get('id', 'unknown')} в планировщик: {e}")
            return None
    def add_task_via_config(self, task_data):
        """Добавление задачи через ConfigManager с автоматической перезагрузкой"""
        if self.config_manager.add_task(task_data):
            # Если служба запущена, перезагружаем задачи
            if self.is_running:
                self.load_jobs_from_config()
            return True
        return False
    
    def update_task_via_config(self, task_id, task_data):
        """Обновление задачи через ConfigManager с автоматической перезагрузкой"""
        if self.config_manager.update_task(task_id, task_data):
            # Если служба запущена, перезагружаем задачи
            if self.is_running:
                self.load_jobs_from_config()
            return True
        return False
    
    def delete_task_via_config(self, task_id):
        """Удаление задачи через ConfigManager с автоматической перезагрузкой"""
        if self.config_manager.delete_task(task_id):
            # Если служба запущена, перезагружаем задачи
            if self.is_running:
                self.load_jobs_from_config()
            return True
        return False