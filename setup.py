from PyInstaller.__main__ import run

if __name__ == '__main__':
    opts = [
        'gui_main.py',
        '--onefile',
        '--windowed',
        '--name=ScreenshotScheduler',
        '--icon=media/icons/icon-256x256.ico'
    ]
    run(opts)