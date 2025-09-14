from screenshoter import take_screenshots_mss
from email_sender import EmailSender

from datetime import datetime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import ConflictingIdError

import logging 
import atexit
import os


logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)


class ScreenshotScheduler:
    def __init__(self, db_path='scheduler.db'):

        


        jobstores = {
            'default': SQLAlchemyJobStore(url=f'sqlite:///{db_path}')
        }

        self.scheduler = BackgroundScheduler(jobstores=jobstores)
        self.jobs = {}
        
        # self.start()
        self.load_existing_jobs()
        atexit.register(self.shutdown)
        self.email_sender = EmailSender()
    
    def is_running(self):
        return self.scheduler.running
    
    def shutdown(self):
        self.scheduler.shutdown()
        print('app ended')
    
    def remove_all_jobs(self):
        try:
            self.scheduler.remove_all_jobs()
            self.jobs.clear()
            logging.info("Все задачи удалены")
            return True
        except Exception as e:
            logging.error(f"Ошибка при удалении всех задач: {e}")
            return False
        
    def load_existing_jobs(self):
                
        try:
            
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                self.jobs[job.id] = job
                logging.info(f'tack loaded {job.id}')
            
                
        except Exception as e:
            logging.error(f'error task {e}')
            self.jobs = {}
                
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
        self.scheduler.start()
        print('launch app')
        for job in self.scheduler.get_jobs():
            self.jobs[job.id] = job
    
    def add_cron_job(self, job_id, hour, minute, days_of_week, args=None):



        try:
            if self.check_job_conflict(job_id):
                self.remove_existing_job(job_id)
            
            
            
        
            days_cron = ','.join(map(str, days_of_week))

            trigger = CronTrigger(
                day_of_week = days_cron,
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
            return job_id
        except ConflictingIdError:
            logging.error(f'Конфликт ID задачи: {job_id}')
            return None
        except Exception as e:
            logging.error(f'Не удалось добавить интервальную задачу {job_id}: {e}')
            return None

    @staticmethod
    def take_screenshot_handler(self, save_dir='screenshots', send_email=False):
        try:
            saved_screens = take_screenshots_mss(save_dir)

            if send_email and saved_screens and self.email_sender.enabled:
                subject = f"Скриншоты от {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                body = "Автоматически отправленные скриншоты"
                self.email_sender.send_email(subject, body, saved_screens)
                
            return saved_screens
        except Exception as e:
            print(f"Ошибка в задаче: {e}")
            return None


    


    # def remove_job(self, job_id):
    #     if job_id in self.jobs:
    #         self.scheduler.remove_job(job_id)
    #         del self.jobs[job_id]
    #         logging.info(f'task {job_id} deleted')  
    #         return True
    #     return False
    
    

  

    def remove_existing_job(self, job_id):
    
        try:
            existing_job = self.scheduler.get_job(job_id)
            if existing_job:
                self.scheduler.remove_job(job_id)
                if job_id in self.jobs:
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
        self.email_sender.configure(smtp_server, smtp_port, username, password, from_addr, to_addr, enabled)