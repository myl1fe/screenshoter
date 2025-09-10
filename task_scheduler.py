from screenshoter import take_screenshots_mss

from datetime import datetime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


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
        

        atexit.register(self.shutdown)
        

    def start(self):
        self.scheduler.start()
        print('launch app')
        for job in self.scheduler.get_jobs():
            self.jobs[job.id] = job
    
    def add_cron_job(self, job_id, hour, minute, days_of_week, job_func, args=None):

        try:
            existing_job = self.scheduler.get_job(job_id)

            if existing_job:
                logging.info(f'Task {job_id} already exists, replace')
                self.scheduler.remove_job(job_id)
                if job_id in self.jobs:
                    del self.jobs[job_id]
        
            days_cron = ','.join(map(str, days_of_week))

            trigger = CronTrigger(
                day_of_week = days_cron,
                hour=hour,
                minute=minute,
                timezone='Europe/Moscow'
            )

            job = self.scheduler.add_job(
                job_func,
                trigger,
                args = args or [],
                id = job_id
            )


            self.jobs[job_id] = job

            print(f'task {job_id} added for {hour} and {minute} by {days_of_week}')
            return job_id
        except Exception as e:
            logging.info(f'failed added task  {job_id}: {e}')
            return None


    def remove_job(self, job_id):
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            print(f'task {job_id} delleted')
            return True
        return False

    def get_jobs(self):
        return self.scheduler.get_jobs()
    def shutdown(self):
        self.scheduler.shutdown()
        print('app ended')

