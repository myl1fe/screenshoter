import sys
import os
import logging
from PyQt5 import QtWidgets, QtGui
from gui import ScreenshotApp

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def handle_exception(exc_type, exc_value, exc_traceback):
    
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    logger.error("Необработанное исключение:", 
                 exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception

def main():
    
    try:
        
        app = QtWidgets.QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        
        
        app.setStyle('Fusion')
        
        
        window = ScreenshotApp()
        window.show()
        
        logger.info("GUI приложение запущено успешно")
        
        
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")
        
        QtWidgets.QMessageBox.critical(None, "Ошибка запуска", 
                                      f"Не удалось запустить приложение:\n{str(e)}")

if __name__ == "__main__":
    main()