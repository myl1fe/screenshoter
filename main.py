import mss
import mss.tools
from datetime import datetime
import os
import time

def take_screenshots_mss(save_dir = 'place_sreen'):
    try:
        os.makedirs(save_dir, exist_ok = True)
        timestap = datetime.now().strftime("%d%m%Y_%H%M%S")
        saved_screen = []

        

        with mss.mss() as sct:
            count_monitors = sct.monitors
        
            if len(count_monitors) > 2:
                
                
                for num, monitors in enumerate(count_monitors[1:], start = 1):
                    filename = os.path.join(save_dir, f'screenshot_{timestap}_monitor_{num}.png')

                    sct_img = sct.grab(monitors)
                    mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)
                    saved_screen.append(filename)



            else:
                filename = os.path.join(save_dir, f'screenshot_{timestap}.png')
                sct_img = sct.grab(count_monitors[1])
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)
                saved_screen.append(filename)

        print('uspeshno')
        return saved_screen
   
   
    except Exception as e:
        print(f'ошибика {e}')
        return None

if __name__ == '__main__':
    result = take_screenshots_mss()
    if result:
        print(f"Созданные файлы: {result}")