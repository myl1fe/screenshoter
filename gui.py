import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QMessageBox
from task_scheduler import ScreenshotScheduler
from screenshoter import take_screenshots_mss
import os
import logging


class ScreenshotApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.scheduler = ScreenshotScheduler("screenshots.db")
        self.setup_gui()
        self.setup_tray()
        self.setup_signals()
        self.populate_jobs_list() 


    def setup_gui(self):
        self.setWindowTitle('скриншотер')
        self.setGeometry(100, 100, 500, 400)


        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)


        time_layout = QtWidgets.QHBoxLayout()
        time_layout.addWidget(QtWidgets.QLabel("Время:"))
        self.time_edit = QtWidgets.QTimeEdit()
        self.time_edit.setTime(QtCore.QTime.currentTime())
        time_layout.addWidget(self.time_edit)
        layout.addLayout(time_layout)

        
        days_group = QtWidgets.QGroupBox("Дни недели")
        days_layout = QtWidgets.QGridLayout()
        
        self.days_checkboxes = []
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


        for i, day in enumerate(days):
            checkbox = QtWidgets.QCheckBox(day)
            if i < 5:  
                checkbox.setChecked(True)
            self.days_checkboxes.append(checkbox)
            days_layout.addWidget(checkbox, i // 4, i % 4)        
        days_group.setLayout(days_layout)
        layout.addWidget(days_group)

        button_layout = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Старт")
        self.stop_btn = QtWidgets.QPushButton("Стоп")
        self.stop_btn.setEnabled(False)


        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        layout.addLayout(button_layout)

        
        self.status_label = QtWidgets.QLabel("Статус: Неактивно")
        layout.addWidget(self.status_label)

        self.jobs_list = QtWidgets.QListWidget()
        layout.addWidget(self.jobs_list)

        self.clear_btn = QtWidgets.QPushButton("Удалить все задачи")
        button_layout.addWidget(self.clear_btn)

        self.conflict_label = QtWidgets.QLabel("")
        self.conflict_label.setStyleSheet("color: red;")
        layout.addWidget(self.conflict_label)
        
        interval_layout = QtWidgets.QHBoxLayout()
        interval_layout.addWidget(QtWidgets.QLabel("Интервал (минуты):"))
        self.interval_spinbox = QtWidgets.QSpinBox()
        self.interval_spinbox.setMinimum(1)
        self.interval_spinbox.setMaximum(1440)  
        self.interval_spinbox.setValue(60)  
        interval_layout.addWidget(self.interval_spinbox)
        
        self.interval_start_btn = QtWidgets.QPushButton("Старт интервал")
        interval_layout.addWidget(self.interval_start_btn)
        
        layout.addLayout(interval_layout)

    def setup_tray(self):

        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(self, "Ошибка", " трей недоступен.")
            return

        self.tray_icon = QSystemTrayIcon(self)

        icon_path_tray = os.path.join('media', 'icons', 'icon-16x16.ico')
        logging.info("Иконка трея установлена.")
        icon_path_panel = os.path.join('media', 'icons', 'icon-32x32.ico')
        #icon_path_shortcut = os.path.join('media', 'icons', 'icon-256x256.ico')

        if os.path.exists(icon_path_tray):
            self.tray_icon.setIcon(QtGui.QIcon(icon_path_tray))
            self.setWindowIcon(QtGui.QIcon(icon_path_panel))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))
            logging.warning(f"Иконка не найдена по пути: {icon_path_tray}")

        self.tray_icon.setVisible(True)       
        
        tray_menu = QMenu()
        show_action = QAction("Показать", self)
        hide_action = QAction("Скрыть", self)
        exit_action = QAction("Выход", self)


        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)

        show_action.triggered.connect(self.show_window)
        hide_action.triggered.connect(self.hide_window)
        exit_action.triggered.connect(self.quit_app)
        
        
        self.tray_icon.activated.connect(self.on_tray_activate)  
    
    def setup_signals(self):

        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn.clicked.connect(self.on_stop)
        self.clear_btn.clicked.connect(self.on_clear_all)
        self.jobs_list.itemClicked.connect(self.on_job_selected)
        self.interval_start_btn.clicked.connect(self.on_interval_start) 



    def on_start(self):
        try:
            
            time_str = self.time_edit.time().toString("HH:mm")
            hour, minute = map(int, time_str.split(":"))
            selected_days = []


            for i, checkbox in enumerate(self.days_checkboxes):
                if checkbox.isChecked():
                    selected_days.append(i)
            if not selected_days:
                QMessageBox.warning(self, 'Необходимо выбрать хотя бы один день')
                return
            
            
            job_id = "scheduled_screenshot"
            if self.scheduler.check_job_conflict(job_id):
                self.conflict_label.setText(f"Задача {job_id} уже существует!")
                reply = QMessageBox.question(
                    self, 
                    "Конфликт задач", 
                    f"Задача {job_id} уже существует. Заменить?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return


            result = self.scheduler.add_cron_job(
                job_id = job_id,
                hour = hour,
                minute = minute,
                days_of_week = selected_days,
                args = ['screenshots']
                )
            
            if result:
                if not self.scheduler.scheduler.running:
                    self.scheduler.start()    
                
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.status_label.setText(f"Статус: Приложение активно запланировано на {time_str}")
                self.conflict_label.setText("")
                self.populate_jobs_list()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось добавить задачу")        
            
                # days_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
                # selected_days_names = [days_names[i] for i in selected_days]
                # self.jobs_list.addItem(f"Скриншот в {time_str} по дням: {', '.join(selected_days_names)}")


            
                
        except Exception as e:
            logging.error(f"Ошибка при запуске планировщика: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить приложение: {str(e)}")

    def on_interval_start(self):
        
        try:
            minutes = self.interval_spinbox.value()
            job_id = "interval_screenshot"
            
            
            if self.scheduler.check_job_conflict(job_id):
                self.conflict_label.setText(f"Задача {job_id} уже существует!")
                reply = QMessageBox.question(
                    self, 
                    "Конфликт задач", 
                    f"Задача {job_id} уже существует. Заменить?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            
            
            result = self.scheduler.add_interval_job(
                job_id=job_id,
                minutes=minutes,
                args=['screenshots']
            )
            
            if result:
                self.scheduler.start()
                self.status_label.setText(f"Статус: Активно - интервал повторений каждые: {minutes} мин")
                self.conflict_label.setText("") 
                self.populate_jobs_list() 
                logging.info(f"Интервальная задача добавлена: каждые {minutes} минут")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось добавить интервальную задачу")
                
        except Exception as e:
            logging.error(f"Ошибка при запуске интервальной задачи: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить интервальную задачу: {str(e)}")

    def on_stop(self):
        try:                
            self.scheduler.shutdown()  
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Статус: Неактивно")
                    
            self.jobs_list.clear()
                    
            logging.info("Планировщик остановлен")
                
        except Exception as e:
            logging.error(f"Ошибка при остановке планировщика: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось остановить планировщик: {str(e)}")

    def on_job_selected(self, item):
    
        job_id = item.text().split(":")[0].strip()
        job_info = self.scheduler.get_detailed_job_info(job_id)
        
        if job_info:
            info_text = f"ID: {job_info['id']}\n"
            info_text += f"Следующий запуск: {job_info['next_run_time']}\n"
            info_text += f"Триггер: {job_info['trigger']}\n"
            info_text += f"Аргументы: {job_info['args']}"
            
            self.status_label.setText(info_text)

    def take_screenshot_wrapper(self):
        
        try:
            
            result = take_screenshots_mss('screenshots')
            
            if result:
                logging.info(f"Скриншоты успешно созданы: {result}")
                
                self.tray_icon.showMessage(
                    "Скриншотер",
                    f"Созданы скриншоты: {len(result)} файлов",
                    QSystemTrayIcon.Information,
                    3000
                )
            else:
                logging.error("Не удалось создать скриншоты")
                
        except Exception as e:
            logging.error(f"Ошибка при создании скриншотов: {e}")
    
    def populate_jobs_list(self):
        self.jobs_list.clear()
        for job_id, job in self.scheduler.jobs.items():
            job_type = "По расписанию" if "cron" in job_id else "По интервалу"
            self.jobs_list.addItem(f"{job_id} ({job_type}): {self.scheduler.get_job_info(job_id)}")

    def on_clear_all(self):
        
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            "Вы уверены, что хотите удалить все задачи?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.scheduler.remove_all_jobs():
                self.populate_jobs_list()
                self.status_label.setText("Статус: Все задачи удалены")
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                QMessageBox.information(self, "Успех", "Все задачи успешно удалены")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить задачи")

    def show_window(self):
        
        self.show()
        self.activateWindow()  
    
    def hide_window(self):
        
        self.hide()
    
    def quit_app(self):
        
        try:
            self.scheduler.shutdown()
        except Exception as e:
            logger.error(f"Ошибка при остановке планировщика: {e}")
        finally:
            QtWidgets.qApp.quit()



    def on_tray_activate(self, reason):
        
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def closeEvent(self, event):
        
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Скриншотер",
            "Приложение свернуто в трей. Для выхода используйте правый клик по иконке.",
            QSystemTrayIcon.Information,
            2000
        )

def main():
    
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  
    window = ScreenshotApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()