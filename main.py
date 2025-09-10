import time
from task_scheduler import ScreenshotScheduler
from screenshoter import take_screenshots_mss


def main():
    scheduler = ScreenshotScheduler()

    scheduler.add_cron_job(
        job_id = 'test_screen_1',
        hour = 16,
        minute = 41,
        days_of_week = [0, 1, 2, 3, 4, 5, 6],
        job_func = take_screenshots_mss,
        args = ['place_sreen']
    )

    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
    
if __name__ == "__main__":
    main()