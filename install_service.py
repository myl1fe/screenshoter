import os
import sys
import subprocess
import shutil
import glob
import platform

print("=== СКРИПТ ЗАПУЩЕН ===")
print(f"Python: {sys.executable}")
print(f"Рабочая папка: {os.getcwd()}")
print(f"Аргументы: {sys.argv}")

def find_nssm():
    """Поиск nssm.exe в различных возможных местах"""
    print("🔍 Поиск NSSM...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Проверяем в текущей директории проекта
    nssm_path = os.path.join(current_dir, "nssm.exe")
    if os.path.exists(nssm_path):
        print(f"✅ NSSM найден в корне: {nssm_path}")
        return nssm_path
    
    # Ищем папки с nssm
    nssm_folders = glob.glob(os.path.join(current_dir, "nssm*"))
    print(f"📁 Найдены папки NSSM: {nssm_folders}")
    
    for folder in nssm_folders:
        if os.path.isdir(folder):
            # Проверяем win64
            win64_path = os.path.join(folder, "win64", "nssm.exe")
            if os.path.exists(win64_path):
                print(f"✅ NSSM найден в: {win64_path}")
                return win64_path
            
            # Проверяем win32
            win32_path = os.path.join(folder, "win32", "nssm.exe")
            if os.path.exists(win32_path):
                print(f"✅ NSSM найден в: {win32_path}")
                return win32_path
    
    print("❌ NSSM не найден!")
    return None

def install_service():
    """Установка службы через NSSM"""
    print("🚀 Запуск установки службы...")
    
    nssm_path = find_nssm()
    
    if not nssm_path:
        print("❌ NSSM не найден!")
        print("📥 Скачайте NSSM с https://nssm.cc/download")
        print("📦 Распакуйте в папку с проектом")
        return False
    
    # Путь к Python и скрипту service_launcher.py
    python_path = sys.executable
    script_path = os.path.abspath("service_launcher.py")
    
    if not os.path.exists(script_path):
        print(f"❌ Файл service_launcher.py не найден: {script_path}")
        return False
        
    print(f"✅ service_launcher.py найден: {script_path}")
    
    service_name = "ScreenshotService"
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Команда установки службы
    cmd = [nssm_path, "install", service_name, python_path, script_path, "service"]
    print(f"🔧 Команда установки: {' '.join(cmd)}")
    
    try:
        print("📦 Установка службы...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        print("✅ Служба успешно установлена!")
        
        # Настройки службы
        subprocess.run([nssm_path, "set", service_name, "DisplayName", "Screenshot Service"], check=True)
        subprocess.run([nssm_path, "set", service_name, "Description", "Автоматическое создание скриншотов"], check=True)
        subprocess.run([nssm_path, "set", service_name, "Start", "SERVICE_AUTO_START"], check=True)
        subprocess.run([nssm_path, "set", service_name, "AppDirectory", project_dir], check=True)
        
        print("\n🎯 Команды управления:")
        print(f"Запуск: nssm start {service_name}")
        print(f"Остановка: nssm stop {service_name}")
        print(f"Статус: nssm status {service_name}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки: {e}")
        if e.stderr:
            print(f"Детали: {e.stderr}")
        return False

def uninstall_service():
    """Удаление службы"""
    print("🗑️ Удаление службы...")
    nssm_path = find_nssm()
    
    if not nssm_path:
        print("❌ NSSM не найден!")
        return False
        
    service_name = "ScreenshotService"
    
    try:
        subprocess.run([nssm_path, "stop", service_name], check=False)
        subprocess.run([nssm_path, "remove", service_name, "confirm"], check=True)
        print("✅ Служба удалена!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка удаления: {e}")
        return False

def service_status():
    """Проверка статуса службы"""
    print("📊 Проверка статуса службы...")
    nssm_path = find_nssm()
    
    if not nssm_path:
        print("❌ NSSM не найден!")
        return False
        
    service_name = "ScreenshotService"
    
    try:
        result = subprocess.run([nssm_path, "status", service_name], capture_output=True, text=True, encoding='utf-8')
        status = result.stdout.strip()
        print(f"📊 Статус службы '{service_name}': {status}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка проверки статуса: {e}")
        return False

def show_help():
    """Показать справку"""
    print("""
🎯 Установщик службы ScreenshotService

Команды:
python install_service.py          - установка службы
python install_service.py uninstall - удаление службы  
python install_service.py status    - проверка статуса
python install_service.py help      - эта справка

Требования:
- NSSM.exe в папке проекта или в nssm-* подпапке
- service_launcher.py в корне проекта
    """)

if __name__ == "__main__":
    print("=== Установщик службы ScreenshotService ===")
    
    # Принудительно сбрасываем буфер вывода
    sys.stdout.flush()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "uninstall":
            uninstall_service()
        elif command == "status":
            service_status()
        elif command == "help":
            show_help()
        else:
            print(f"❌ Неизвестная команда: {command}")
            show_help()
    else:
        install_service()
    
    print("=== Завершение работы ===")