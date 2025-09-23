import win32serviceutil
import win32service
import win32event
import win32api
import win32con
import time
import sys
import os
from pathlib import Path

def install_service_with_timeout():
    """Установка службы с увеличенным временем ожидания"""
    try:
        
        python_exe = sys.executable
        script_path = os.path.abspath("windows_service.py")
        
        
        service_name = "ScreenshotScheduler"
        
       
        win32serviceutil.InstallService(
            python_exe,
            service_name,
            "Screenshot Scheduler Service",
            startType=win32service.SERVICE_AUTO_START
        )
        
        
        import win32api
        import win32con
        
        
        reg_path = f"SYSTEM\\CurrentControlSet\\Services\\{service_name}"
        
        
        key = win32api.RegOpenKeyEx(
            win32con.HKEY_LOCAL_MACHINE,
            reg_path,
            0,
            win32con.KEY_ALL_ACCESS
        )
        
        
        win32api.RegSetValueEx(
            key,
            "ServicesPipeTimeout",
            0,
            win32con.REG_DWORD,
            60000
        )
        
        win32api.RegCloseKey(key)
        
        print("Служба установлена с увеличенным таймаутом (60 секунд)")
        return True
        
    except Exception as e:
        print(f"Ошибка установки службы: {e}")
        return False

if __name__ == "__main__":
    install_service_with_timeout()