import mss
import mss.tools
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


def take_screenshots_mss(save_dir = 'place_sreen'):
    try:
        abs_path = os.path.abspath(save_dir)
        logging.info(f"Сохранение скриншотов в: {abs_path}")
        
        os.makedirs(abs_path, exist_ok=True)
        timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
        saved_screen = []

        

        with mss.mss() as sct:
            count_monitors = sct.monitors

            logging.info(f'Обнаружено мониторов: {len(count_monitors) - 1}')
        
            if len(count_monitors) > 2:
                
                
                for num, monitors in enumerate(count_monitors[1:], start = 1):
                    filename = os.path.join(save_dir, f'screenshot_{timestamp}_monitor_{num}.png')
                    logging.info(f'Создание скриншота {num} для монитора {filename}')


                    sct_img = sct.grab(monitors)
                    mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)
                    logging.info(f"Создание скриншота: {filename}")
                    saved_screen.append(filename)
                    logging.info(f"Скриншот сохранен: {filename}")



            else:
                filename = os.path.join(save_dir, f'screenshot_{timestamp}.png')
                logging.info(f'Создание скриншота: {filename}')
                
                sct_img = sct.grab(count_monitors[1])
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)
                
                saved_screen.append(filename)
                logging.info(f"Скриншот сохранен: {filename}")

        logging.info(f"Успешно создано {len(saved_screen)} скриншотов")
        return saved_screen
   
   
    except Exception as e:
        with open("screenshot_errors.log", "a") as log_file:
            log_file.write(f"{datetime.now()}: {e}\n")
        return None

if __name__ == '__main__':
    result = take_screenshots_mss()
    if result:
        print(f"Созданные файлы: {result}")