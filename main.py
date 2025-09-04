import mss
from datetime import datetime
import os

def take_screenshots_mss(save_dir = 'place_sreen'):
    try:
        os.makedirs(save_dir, exist_ok = True)
        timestap = datetime.now().strftime("%d$m$Y_%H%M%S")
        filename = os.path.join(save_dir, f'screenshot_{timestap}.png')


        with mss.mss() as sct:
            filename = sct.shot(output = filename)

        print('uspeshno')
        return filename
    except Exception as e:
        print(f'ошибика {e}')
        return None

if __name__ == '__main__':
    take_screenshots_mss()