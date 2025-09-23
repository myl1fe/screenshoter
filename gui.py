import os
import logging
from datetime import datetime
import sys

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QMessageBox
from task_scheduler import ScreenshotScheduler
from screenshoter import take_screenshots_mss




class ScreenshotApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.scheduler = ScreenshotScheduler()
        self.setup_gui()
        self.setup_tray()
        self.setup_signals()
        self.load_email_settings()
        self.populate_jobs_list() 

    
    def setup_gui(self):
        self.setWindowTitle('скриншотер')
        self.setGeometry(100, 100, 600, 500)  # Увеличим высоту для новых элементов

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Вкладки для организации интерфейса
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)
        
        # Основная вкладка
        main_tab = QtWidgets.QWidget()
        self.tabs.addTab(main_tab, "Основные настройки")
        main_layout = QtWidgets.QVBoxLayout(main_tab)
        
        # Вкладка для email
        email_tab = QtWidgets.QWidget()
        self.tabs.addTab(email_tab, "Настройки email")
        email_layout = QtWidgets.QVBoxLayout(email_tab)

        # Основные настройки (на первой вкладке)
        time_layout = QtWidgets.QHBoxLayout()
        time_layout.addWidget(QtWidgets.QLabel("Время:"))
        self.time_edit = QtWidgets.QTimeEdit()
        self.time_edit.setTime(QtCore.QTime.currentTime())
        time_layout.addWidget(self.time_edit)
        main_layout.addLayout(time_layout)

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
        main_layout.addWidget(days_group)

        # Чекбокс для отправки email (на основной вкладке)
        self.email_cron_checkbox = QtWidgets.QCheckBox("Отправить скриншот по email")
        main_layout.addWidget(self.email_cron_checkbox)

        button_layout = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Запустить по расписанию")
        self.stop_btn = QtWidgets.QPushButton("Стоп")
        self.stop_btn.setEnabled(False)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        main_layout.addLayout(button_layout)

        self.status_label = QtWidgets.QLabel("Статус: Неактивно")
        main_layout.addWidget(self.status_label)

        self.jobs_list = QtWidgets.QListWidget()
        main_layout.addWidget(self.jobs_list)

        self.clear_btn = QtWidgets.QPushButton("Удалить все задачи")
        button_layout.addWidget(self.clear_btn)

        self.conflict_label = QtWidgets.QLabel("")
        self.conflict_label.setStyleSheet("color: red;")
        main_layout.addWidget(self.conflict_label)
        
        # Интервальные настройки (на основной вкладке)
        interval_group = QtWidgets.QGroupBox("Интервальный режим")
        interval_layout = QtWidgets.QHBoxLayout()
        
        interval_layout.addWidget(QtWidgets.QLabel("Интервал (минуты):"))
        self.interval_spinbox = QtWidgets.QSpinBox()
        self.interval_spinbox.setMinimum(1)
        self.interval_spinbox.setMaximum(1440)  
        self.interval_spinbox.setValue(60)  
        interval_layout.addWidget(self.interval_spinbox)
        
        self.interval_start_btn = QtWidgets.QPushButton("Запустить по интервалу")
        interval_layout.addWidget(self.interval_start_btn)
        
        self.email_interval_checkbox = QtWidgets.QCheckBox("Отправить скриншот по email")
        interval_layout.addWidget(self.email_interval_checkbox)
        
        interval_group.setLayout(interval_layout)
        main_layout.addWidget(interval_group)

        # Настройки email (на второй вкладке)
        email_settings_group = QtWidgets.QGroupBox("Настройки SMTP")
        email_settings_layout = QtWidgets.QGridLayout()
        
        email_settings_layout.addWidget(QtWidgets.QLabel("SMTP сервер:"), 0, 0)
        self.smtp_server_edit = QtWidgets.QLineEdit("smtp.gmail.com")
        email_settings_layout.addWidget(self.smtp_server_edit, 0, 1)
        
        email_settings_layout.addWidget(QtWidgets.QLabel("Порт:"), 1, 0)
        self.smtp_port_edit = QtWidgets.QSpinBox()
        self.smtp_port_edit.setRange(1, 65535)
        self.smtp_port_edit.setValue(587)
        email_settings_layout.addWidget(self.smtp_port_edit, 1, 1)
        
        email_settings_layout.addWidget(QtWidgets.QLabel("Логин:"), 2, 0)
        self.email_login_edit = QtWidgets.QLineEdit()
        email_settings_layout.addWidget(self.email_login_edit, 2, 1)
        
        email_settings_layout.addWidget(QtWidgets.QLabel("Пароль:"), 3, 0)
        self.email_password_edit = QtWidgets.QLineEdit()
        self.email_password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        email_settings_layout.addWidget(self.email_password_edit, 3, 1)
        
        email_settings_layout.addWidget(QtWidgets.QLabel("От кого:"), 4, 0)
        self.email_from_edit = QtWidgets.QLineEdit()
        email_settings_layout.addWidget(self.email_from_edit, 4, 1)
        
        email_settings_layout.addWidget(QtWidgets.QLabel("Кому:"), 5, 0)
        self.email_to_edit = QtWidgets.QLineEdit()
        email_settings_layout.addWidget(self.email_to_edit, 5, 1)
        
        self.email_enabled_checkbox = QtWidgets.QCheckBox("Включить отправку email")
        email_settings_layout.addWidget(self.email_enabled_checkbox, 6, 0, 1, 2)
        
        self.test_email_btn = QtWidgets.QPushButton("Тест отправки email")
        email_settings_layout.addWidget(self.test_email_btn, 7, 0, 1, 2)
        
        email_settings_group.setLayout(email_settings_layout)
        email_layout.addWidget(email_settings_group)

        self.test_email_btn = QtWidgets.QPushButton("Тест отправки email")
        email_settings_layout.addWidget(self.test_email_btn, 7, 0, 1, 2)
        
        # Загрузка сохраненных настроек
        self.load_email_settings()


        
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
        self.jobs_list.itemDoubleClicked.connect(self.on_job_double_clicked)
        self.test_email_btn.clicked.connect(self.on_test_email) 
        
        



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
            
            if not selected_days:
                QMessageBox.warning(self, 'Необходимо выбрать хотя бы один день')
                return

            email_enabled = self.email_enabled_checkbox.isChecked()
            send_email = self.email_cron_checkbox.isChecked()
            if send_email and not email_enabled:
                QMessageBox.warning(self, 'Ошибка', 
                               'Для отправки email необходимо включить опцию "Включить отправку email" в настройках')
                return

            #настрйки email
            self.scheduler.configure_email(
            self.smtp_server_edit.text(),
            self.smtp_port_edit.value(),
            self.email_login_edit.text(),
            self.email_password_edit.text(),
            self.email_from_edit.text(),
            self.email_to_edit.text(),
            email_enabled
        )           
            self.save_email_settings()

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
                args = ['screenshots', send_email]
                )
            
            if result:
                if not self.scheduler.is_running():
                    self.scheduler.start()    
                
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.status_label.setText(f"Статус: Приложение активно запланировано на {time_str}")
                self.conflict_label.setText("")
                self.populate_jobs_list()
                self.tray_icon.showMessage(
                "Скриншотер",
                f"Задача запущена. Скриншоты будут создаваться в {time_str} по выбранным дням.",
                QSystemTrayIcon.Information,
                3000
            )
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось добавить задачу")        
            
            #конфигурация для email




            
                
        except Exception as e:
            logging.error(f"Ошибка при запуске планировщика: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить приложение: {str(e)}")

    def on_interval_start(self):
        try:
            
            minutes = self.interval_spinbox.value()            
            job_id = f"interval_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            #настраиваем email
            email_enabled = self.email_enabled_checkbox.isChecked()
            send_email = self.email_interval_checkbox.isChecked()
            
            if send_email and not email_enabled:
                QMessageBox.warning(self, 'Ошибка', 
                                'Для отправки email необходимо включить опцию "Включить отправку email" в настройках')
                return
                
            #настройки email
            self.scheduler.configure_email(
                self.smtp_server_edit.text(),
                self.smtp_port_edit.value(),
                self.email_login_edit.text(),
                self.email_password_edit.text(),
                self.email_from_edit.text(),
                self.email_to_edit.text(),
                email_enabled
            )
            
            
            self.save_email_settings()
            
            
            result = self.scheduler.add_interval_job(
                job_id=job_id,
                minutes=minutes,
                args=['screenshots', send_email]  
            )
            
            if result:
                
                if not self.scheduler.is_running():
                    logging.info("Запускаем планировщик...")
                    self.scheduler.start()
                    logging.info("Планировщик запущен")
                else:
                    logging.info("Планировщик уже запущен")
                    
                #
                self.status_label.setText(f"Статус: Активно - интервал повторений каждые: {minutes} мин")
                self.conflict_label.setText("") 
                self.populate_jobs_list()
                
                #
                self.tray_icon.showMessage(
                    "Скриншотер",
                    f"Интервальная задача запущена. Скриншоты будут создаваться каждые {minutes} минут.",
                    QSystemTrayIcon.Information,
                    3000
                )
                
                logging.info(f"Интервальная задача добавлена: каждые {minutes} минут")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось добавить интервальную задачу")
                
        except Exception as e:
            logging.error(f"Ошибка при запуске интервальной задачи: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить интервальную задачу: {str(e)}")

    def on_stop(self):
        try: 
            if not self.scheduler.is_running():  
                self.scheduler.start()  
               
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
        if not job_id:  
            QMessageBox.warning(self, "Ошибка", "Не удалось определить ID задачи")
            return
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
             
        for job_id in self.scheduler.jobs.keys():

            widget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout(widget)


            job_info = self.scheduler.get_job_info(job_id)
            label = QtWidgets.QLabel(f"{job_id}: {job_info}")
            layout.addWidget(label)

            stop_btn = QtWidgets.QPushButton("Стоп")
            stop_btn.clicked.connect(lambda checked, id=job_id: self.stop_single_job(id))
            layout.addWidget(stop_btn)

            item = QtWidgets.QListWidgetItem(self.jobs_list)
            item.setSizeHint(widget.sizeHint())
            self.jobs_list.setItemWidget(item, widget)
        
            if job_id.startswith('interval_screenshot'):
                task_type = "Интервальная"
            else:
                task_type = "По расписанию"
                
            item_text = f"{task_type}: ID: {job_id}, {job_info}"
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.UserRole, job_id)
            self.jobs_list.addItem(item)

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
            logging.error(f"Ошибка при остановке планировщика: {e}")
        finally:
            QtWidgets.qApp.quit()



    def on_job_double_clicked(self, item):
    # Получаем job_id из данных элемента
        job_id = item.data(QtCore.Qt.UserRole)
        if not job_id:
            QMessageBox.warning(self, "Ошибка", "Не удалось определить ID задачи")
            return

        reply = QMessageBox.question(
            self, 
            "Удаление задачи", 
            f"Удалить задачу {job_id}?",
            QMessageBox.Yes | QMessageBox.No
        )   
        
        if reply == QMessageBox.Yes:
            if self.scheduler.remove_existing_job(job_id):
                self.populate_jobs_list()
                QMessageBox.information(self, "Успех", f"Задача {job_id} удалена")
            else:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить задачу {job_id}")
   

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

    def save_email_settings(self):
    
        settings = QtCore.QSettings("Screenshoter", "EmailSettings")
        settings.setValue("smtp_server", self.smtp_server_edit.text())
        settings.setValue("smtp_port", self.smtp_port_edit.value())
        settings.setValue("email_login", self.email_login_edit.text())
        settings.setValue("email_from", self.email_from_edit.text())
        settings.setValue("email_to", self.email_to_edit.text())
        settings.setValue("email_enabled", self.email_enabled_checkbox.isChecked())
        logging.info("Настройки email сохранены")

    def load_email_settings(self):
        
        settings = QtCore.QSettings("Screenshoter", "EmailSettings")
        self.smtp_server_edit.setText(settings.value("smtp_server", "smtp.gmail.com"))
        self.smtp_port_edit.setValue(int(settings.value("smtp_port", 587)))
        self.email_login_edit.setText(settings.value("email_login", ""))
        self.email_from_edit.setText(settings.value("email_from", ""))
        self.email_to_edit.setText(settings.value("email_to", ""))
        self.email_enabled_checkbox.setChecked(settings.value("email_enabled", False, type=bool))
        logging.info("Настройки email загружены")

    def on_test_email(self):
        
        try:
            
            smtp_server = self.smtp_server_edit.text()
            smtp_port = self.smtp_port_edit.value()
            username = self.email_login_edit.text()
            password = self.email_password_edit.text()
            from_addr = self.email_from_edit.text()
            to_addr = self.email_to_edit.text()
            enabled = self.email_enabled_checkbox.isChecked()
            
            
            self.save_email_settings()
            
            
            self.scheduler.configure_email(smtp_server, smtp_port, username, password, 
                                        from_addr, to_addr, enabled)
            
            
            logging.info("Создание тестового скриншота...")
            test_screenshots = take_screenshots_mss('test_screenshots')
            
            if not test_screenshots:
                QMessageBox.critical(self, "Ошибка", "Не удалось создать тестовый скриншот")
                return
                
            
            logging.info("Отправка тестового email...")
            success = self.scheduler.email_sender.send_email(
                "Тестовое письмо от Скриншотера",
                "Это тестовое письмо было отправлено для проверки настроек email.\n\n"
                "Если вы получили это письмо со скриншотом, значит настройки корректны!",
                test_screenshots
            )
            
            if success:
                QMessageBox.information(self, "Успех", 
                                    "Тестовое письмо отправлено успешно!\n\n"
                                    "Проверьте вашу почту (и папку 'Спам').")
            else:
                QMessageBox.critical(self, "Ошибка", 
                                "Не удалось отправить тестовое письмо.\n\n"
                                "Проверьте настройки SMTP и подключение к интернету.")
                
        except Exception as e:
            logging.error(f"Ошибка при тестировании email: {e}")
            QMessageBox.critical(self, "Ошибка", 
                            f"Ошибка при тестировании email:\n{str(e)}")

    def stop_single_job(self, job_id):
   
        try:
            
            if self.scheduler.remove_existing_job(job_id):
                logging.info(f"Задача {job_id} остановлена и удалена")
                self.populate_jobs_list()  
                self.status_label.setText(f"Задача {job_id} остановлена")
            else:
                logging.error(f"Не удалось найти или удалить задачу {job_id}")
        except Exception as e:
            logging.error(f"Ошибка при остановке задачи {job_id}: {e}")

    
        

def main():
    
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  
    window = ScreenshotApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()