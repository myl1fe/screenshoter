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
        self.config_manager = ConfigManager(config_path)
        self.is_service = self.check_service_mode()
        self.setup_logging()

        # self.is_service = self.check_service_mode()
        # if self.is_service:
        #     self.setup_service_logging()
        # else:
        #     self.setup_app_logging()
        #      
        self.load_jobs_from_config()
        
        # Мониторинг изменений конфига
        self.config_monitor_thread = None
        self.is_running = False

        jobstores = {
            'default': MemoryJobStore()
        }        
        self.scheduler = BackgroundScheduler(jobstores=jobstores)
        self.jobs = {}   
 
        atexit.register(self.shutdown)
        self.email_sender = EmailSender()
        self.config_path = Path("config.json")
        self.last_config_mod_time = 0
        self.config_monitor_thread = None
        self.is_running = False
        
        # Загружаем задачи из конфига при старте
        self.load_jobs_from_config()

    
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
                saved_screens = take_screenshots_mss(save_dir)
                if saved_screens:
                    logging.info(f"Скриншоты созданы: {saved_screens}")
                    
                    if send_email:
                        subject = f"Скриншоты от {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        body = "Автоматически отправленные скриншоты"
                        self.email_sender.send_email(subject, body, saved_screens)
                    
                        #send_screenshot_email(saved_screens, "Запланированные: ")
                        
                    return saved_screens
            except Exception as e:
                print(f"Ошибка в задаче: {e}")
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
                    logging.StreamHandler()
                ]
            )
        else:
            logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    def load_jobs_from_config(self):        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Здесь парсим конфиг и добавляем задачи в планировщик
                # Пример (адаптируйте под структуру вашего конфига):
                jobs = config.get('jobs', [])
                for job in jobs:
                    if job.get('enabled', True):
                        # Добавляем задачу в планировщик
                        # Используйте ваши существующие методы add_interval_job/add_cron_job
                        pass
                        
                logging.info(f"Загружено {len(jobs)} задач из конфига")
                
        except Exception as e:
            logging.error(f"Ошибка загрузки задач из конфига: {e}")
    
    def add_job_from_config(self, job_config):
        """Добавление задачи из конфигурации"""
        try:
            job_id = job_config['id']
            job_type = job_config['type']
            args = [job_config.get('save_dir', 'screenshots'), job_config.get('send_email', False)]
            
            if job_type == 'interval':
                minutes = job_config.get('minutes', 5)
                self.add_interval_job(job_id, minutes, args)
            elif job_type == 'cron':
                hour = job_config.get('hour', 0)
                minute = job_config.get('minute', 0)
                days_of_week = job_config.get('days_of_week', [1,2,3,4,5])
                self.add_cron_job(job_id, hour, minute, days_of_week, args)
                
        except Exception as e:
            logging.error(f"Ошибка добавления задачи {job_config.get('id', 'unknown')}: {e}")
    
    def start_config_monitor(self):
        """Запуск мониторинга изменений конфига"""
        while self.is_running:
            try:
                if self.config_path.exists():
                    current_mod_time = self.config_path.stat().st_mtime
                    if current_mod_time > self.last_config_mod_time:
                        logging.info("Обнаружены изменения в конфиге, перезагружаем задачи...")
                        self.load_jobs_from_config()
                        self.last_config_mod_time = current_mod_time
                
                time.sleep(10)  # Проверяем каждые 10 секунд
            except Exception as e:
                logging.error(f"Ошибка мониторинга конфига: {e}")
                time.sleep(30)
    
    def _monitor_config_changes(self):
        """Мониторинг изменений в конфиг файле"""
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
        
        if not self.scheduler.running:
            self.scheduler.start()
            self.start_config_monitor()
            logging.info("Планировщик запущен с мониторингом конфига")
    
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


    # def configure_email(self, smtp_server, smtp_port, username, password, from_addr, to_addr, enabled):
        # self.configure_email_settings(smtp_server, smtp_port, username, password, from_addr, to_addr, enabled)
    # def is_running(self):
    #     return self.scheduler.running
    