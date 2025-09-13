from screenshoter import take_screenshots_mss

from datetime import datetime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import ConflictingIdError

import logging 
import atexit
import os


logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)


class ScreenshotScheduler:
    def __init__(self, db_path='scheduler.db'):

        self.load_existing_jobs()


        jobstores = {
            'default': SQLAlchemyJobStore(url=f'sqlite:///{db_path}')
        }

        self.scheduler = BackgroundScheduler(jobstores=jobstores)
        self.jobs = {}
        
        self.start()
        atexit.register(self.shutdown)
    
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
            
            
            # existing_job = self.scheduler.get_job(job_id)
            # if existing_job:
            #     logging.info(f'Task {job_id} already exists, replace')
            #     self.scheduler.remove_job(job_id)
            #     if job_id in self.jobs:
            #         del self.jobs[job_id]
        
            days_cron = ','.join(map(str, days_of_week))

            trigger = CronTrigger(
                day_of_week = days_cron,
                hour=hour,
                minute=minute,
                timezone='Europe/Moscow'
            )

            job = self.scheduler.add_job(
                lambda: self.take_screenshot_handler,
                trigger,
                args = args, #or [],
                id = job_id
            )


            self.jobs[job_id] = job

            logging.info(f'task {job_id} added for {hour} and {minute} by {days_of_week}')
            return job_id
        
        except Exception as e:
            logging.info(f'failed added task  {job_id}: {e}')
            return None
        except Exception as e:
            logging.error(f'Не удалось добавить задачу {job_id}: {e}')
            return None

    def add_interval_job(self, job_id, minutes, args=None):
        try:
            
            if self.check_job_conflict(job_id):
                self.remove_existing_job(job_id)
            
            trigger = IntervalTrigger(minutes=minutes)

            job = self.scheduler.add_job(
                lambda: self._execute_screenshot_task(args),
                trigger,
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
    def take_screenshot_handler(self, save_dir='screenshots'):
        try:
            take_screenshots_mss(save_dir)
        except Exception as e:
            print(f"Ошибка в задаче: {e}")


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


        def remove_job(self, job_id):
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                print(f'task {job_id} delleted')
                return True
            return False
    
    

  

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