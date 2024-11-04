import os
import sys
import json
import filecmp
import shutil
import asyncio
import websockets
import threading
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit,
    QMessageBox, QMainWindow, QFormLayout, QDialog, QTextEdit, QSpinBox,
    QComboBox, QFileDialog, QListWidget, QListWidgetItem, QInputDialog,
    QTableWidget, QTableWidgetItem, QHBoxLayout
)
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt
from scripts.database import Database
from scripts.utils import start_websocket_server, connected_students

# Constants
DB_PATH = "lab_work.db"
NEW_DB_PATH = "lab_work_new.db"

async def main():
    # Создаем задачу для WebSocket-сервера
    asyncio.create_task(start_websocket_server())

    # Инициализируем и запускаем приложение Qt
    app = QApplication(sys.argv)
    window = LabWorkApp()
    window.show()
    app.exec()
class LabWorkApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database(DB_PATH)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Приложение для преподавателя")
        self.setGeometry(0, 0, 1920, 1080)
        self.setStyleSheet("background-color: #f0f0f0;")
        font = QFont("Arial", 14)
        self.setFont(font)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        button_style = self.get_button_style()

        # Кнопки для управления функционалом
        lab_button = QPushButton("Лабораторные работы")
        lab_button.setStyleSheet(button_style)
        lab_button.clicked.connect(self.open_lab_work_manager)
        layout.addWidget(lab_button)

        track_button = QPushButton("Отслеживание результатов")
        track_button.setStyleSheet(button_style)
        track_button.clicked.connect(self.track_results)
        layout.addWidget(track_button)

        stats_button = QPushButton("Статистика студентов")
        stats_button.setStyleSheet(button_style)
        stats_button.clicked.connect(self.show_students_results)
        layout.addWidget(stats_button)

        update_button = QPushButton("Обновить базу данных")
        update_button.setStyleSheet(button_style)
        update_button.clicked.connect(self.update_lab_works)
        layout.addWidget(update_button)

    def get_button_style(self) -> str:
        return (
            "QPushButton {"
            "background-color: #4CAF50;"
            "color: white;"
            "border-radius: 10px;"
            "padding: 10px;"
            "font-size: 16px;"
            "font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "background-color: #45a049;"
            "}"
        )

    # Методы для отображения окон

    def open_lab_work_manager(self):
        """Открывает менеджер лабораторных работ и билетов."""
        lab_dialog = QDialog(self)
        lab_dialog.setWindowTitle("Лабораторные работы")
        lab_dialog.setGeometry(500, 300, 500, 400)
    
        layout = QVBoxLayout(lab_dialog)

        # Список существующих билетов
        tickets_list = QListWidget()
        tickets = self.db.get_all_tickets()  # Метод для получения всех билетов из БД
        for ticket in tickets:
            item = QListWidgetItem(f"Лаб. работа {ticket['work_number']} - {ticket['question_type']}")
            item.setData(Qt.UserRole, ticket['ticket_id'])
            tickets_list.addItem(item)

        layout.addWidget(tickets_list)

        # Кнопка для создания нового билета
        add_button = QPushButton("Создать новый билет")
        add_button.setStyleSheet(self.get_button_style())
        add_button.clicked.connect(lambda: self.manage_ticket())
        layout.addWidget(add_button)

        # Открытие редактора для выбранного билета
        tickets_list.itemDoubleClicked.connect(
            lambda item: self.manage_ticket(item.data(Qt.UserRole))
        )

        lab_dialog.setLayout(layout)
        lab_dialog.exec()

    def manage_ticket(self, ticket_id=None):
        """Создает или редактирует билет лабораторной работы."""
        ticket_data = self.db.get_lab_ticket(ticket_id) if ticket_id else None
        editor = self.ticket_editor_dialog(ticket_data)
        editor.exec()

        if editor.result() == QDialog.Accepted:
            data = editor.get_data()
            if ticket_id:
                self.db.update_lab_ticket(ticket_id, **data)
                QMessageBox.information(self, "Успех", "Билет успешно обновлен.")
            else:
                self.db.add_lab_ticket(**data)
                QMessageBox.information(self, "Успех", "Новый билет успешно добавлен.")
            self.open_lab_work_manager()  # Обновляем список билетов
    def ticket_editor_dialog(self, ticket_data=None):
        """Создает диалог для редактирования или создания билета с поддержкой изображений и тематики."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать билет" if ticket_data else "Создать новый билет")
        dialog.setGeometry(500, 300, 600, 700)
    
        layout = QFormLayout(dialog)
    
        # Поле для темы лабораторной работы
        theme_input = QLineEdit()
        theme_input.setText(ticket_data.get("theme", "") if ticket_data else "")
        layout.addRow("Тема лабораторной работы:", theme_input)

        # Поле для номера лабораторной работы
        work_number_input = QSpinBox()
        work_number_input.setMinimum(1)
        work_number_input.setMaximum(1000)
        work_number_input.setValue(ticket_data.get("work_number", 1) if ticket_data else 1)
        layout.addRow("Номер лабораторной работы:", work_number_input)

        # Поле для выбора типа вопроса
        question_type_input = QComboBox()
        question_type_input.addItems(["Теоретический", "Практический", "Графический"])
        if ticket_data:
            question_type_input.setCurrentText(ticket_data.get("question_type", ""))
        layout.addRow("Тип вопроса:", question_type_input)

        # Поле для текста вопроса
        question_text_input = QTextEdit()
        question_text_input.setPlainText(ticket_data.get("question_text", "") if ticket_data else "")
        layout.addRow("Текст вопроса:", question_text_input)

        # Фиксированные 4 варианта ответов с возможностью добавления изображений
        answer_options_widgets = []
        for i in range(4):
            answer_layout = QHBoxLayout()
        
            # Поле ввода текста ответа
            answer_text = QLineEdit(ticket_data["answer_options"][i] if ticket_data and len(ticket_data["answer_options"]) > i else "")
            answer_layout.addWidget(answer_text)

            # Кнопка для добавления/замены изображения
            image_button = QPushButton("Добавить изображение")
            image_path = ticket_data["answer_images"][i] if ticket_data and len(ticket_data["answer_images"]) > i else None
            image_button.clicked.connect(lambda _, b=image_button: self.select_image(b))
            if image_path:
                image_button.setText("Изображение выбрано")
                image_button.setProperty("image_path", image_path)
            answer_layout.addWidget(image_button)

            # Кнопка для удаления изображения
            remove_image_button = QPushButton("Удалить изображение")
            remove_image_button.clicked.connect(lambda _, b=image_button: self.remove_image(b))
            answer_layout.addWidget(remove_image_button)

            answer_options_widgets.append((answer_text, image_button))
            layout.addRow(f"Вариант ответа {i + 1}:", answer_layout)

        # Кнопка для сохранения
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(dialog.accept)
        layout.addWidget(save_button)

        dialog.setLayout(layout)

        # Метод для получения данных из диалога
        def get_data():
            # Получаем путь к изображению вопроса, если оно выбрано
            question_image_path = self.question_image_button.property("image_path") if hasattr(self, 'question_image_button') else None

            return {
                "theme": theme_input.text(),
                "work_number": work_number_input.value(),
                "question_type": question_type_input.currentText(),
                "question_text": question_text_input.toPlainText(),
                "question_image": question_image_path,
                "answer_options": [answer_text.text() for answer_text, _ in answer_options_widgets],
                "answer_images": [image_button.property("image_path") for _, image_button in answer_options_widgets]
            }

        dialog.get_data = get_data
        return dialog

    def select_image(self, button):
        image_path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if image_path:
            button.setText("Изображение выбрано")
            button.setProperty("image_path", image_path)
    
    def remove_image(self, button):
        button.setText("Добавить изображение")
        button.setProperty("image_path", None)

    def get_button_style(self) -> str:
        return (
            "QPushButton {"
            "background-color: #4CAF50;"
            "color: white;"
            "border-radius: 5px;"
            "padding: 5px 10px;"
            "}"
            "QPushButton:hover {"
            "background-color: #45a049;"
            "}"
        )


    def track_results(self):
        """Открывает окно отслеживания результатов в реальном времени."""
        self.track_window = QWidget()
        self.track_window.setWindowTitle("Отслеживание результатов в реальном времени")
        layout = QVBoxLayout(self.track_window)
        layout.addWidget(QLabel("Подключенные студенты:"))
        
        for student_info in connected_students.copy():
            layout.addWidget(QLabel(student_info))
        
        self.track_window.setLayout(layout)
        self.track_window.setGeometry(460, 290, 1000, 600)
        self.track_window.show()

    def show_students_results(self):
        """Открывает окно с результатами студентов."""
        student_results = self.db.get_student_results()
        if not student_results:
            QMessageBox.information(self, "Нет данных", "Нет данных для отображения.")
            return

        table = QTableWidget(len(student_results), 4)
        table.setHorizontalHeaderLabels(["ID", "Имя студента", "Номер лабораторной работы", "Оценка"])
        
        for i, result in enumerate(student_results):
            for j, item in enumerate(result):
                table.setItem(i, j, QTableWidgetItem(str(item)))
        
        layout = QVBoxLayout()
        layout.addWidget(table)
        
        self.results_window = QWidget()
        self.results_window.setWindowTitle("Результаты студентов")
        self.results_window.setLayout(layout)
        self.results_window.setGeometry(460, 290, 1000, 600)
        self.results_window.show()

    def update_lab_works(self):
        """Проверяет и обновляет базу данных, если найдены изменения."""
        try:
            if not filecmp.cmp(DB_PATH, NEW_DB_PATH, shallow=False):
                reply = QMessageBox.question(
                    self, 'Обновить базу данных', 
                    "Обнаружены изменения в базе данных. Обновить базу данных?", 
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    shutil.copy(NEW_DB_PATH, DB_PATH)
                    QMessageBox.information(self, "Успех", "База данных успешно обновлена.")
                    asyncio.run(self.send_updated_db())
            else:
                QMessageBox.information(self, "Нет изменений", "Изменений в базе данных не обнаружено.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении базы данных: {str(e)}")

    async def send_updated_db(self):
        """Отправляет обновленную базу данных через WebSocket."""
        uri = "ws://localhost:5678"
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with websockets.connect(uri) as websocket:
                    with open(DB_PATH, 'rb') as f:
                        data = f.read()
                    await websocket.send(json.dumps({"type": "update_db", "data": data.decode('latin1')}))
                    await websocket.recv()
                    QMessageBox.information(self, "Успех", "Обновленная база данных отправлена устройствам.")
                    return
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось отправить базу данных: {str(e)}")

    def add_answer_option(self, answer_options_list: QListWidget) -> None:
        """Добавляет новый вариант ответа (текстовый или графический)."""
        answer_text, ok = QInputDialog.getText(self, "Добавить вариант ответа", "Введите текст ответа:")
        if ok and answer_text:
            item = QListWidgetItem(answer_text)
            answer_options_list.addItem(item)
        else:
            image_path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение для ответа", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
            if image_path:
                item = QListWidgetItem("[Изображение] " + os.path.basename(image_path))
                item.setData(Qt.UserRole, image_path)
                answer_options_list.addItem(item)

    def create_save_button(self, work_id, editor):
        save_button = QPushButton("Сохранить изменения")
        save_button.setStyleSheet(self.get_button_style())
        save_button.clicked.connect(lambda: self.save_lab_work(work_id, editor))
        return save_button

    def format_lab_work(self, work):
        return (
            f"ID: {work[0]}\nНомер работы: {work[1]}\nНомер вопроса: {work[2]}\n"
            f"Тип вопроса: {work[3]}\nТекст вопроса: {work[4]}\nВарианты ответов: {work[5]}"
        )

    def save_lab_work(self, lab_work_id, editor):
        """Сохраняет изменения в лабораторной работе."""
        try:
            content = editor.toPlainText().split('\n')
            work_number = int(content[1].split(': ')[1])
            question_number = int(content[2].split(': ')[1])
            question_type = content[3].split(': ')[1]
            question_text = content[4].split(': ')[1]
            answer_options = json.loads(content[5].split(': ')[1])

            # Сохранение изменений в базе данных
            self.db.update_lab_work(
                lab_work_id, work_number, question_number,
                question_type, question_text, answer_options
            )
            QMessageBox.information(self, "Успех", "Лабораторная работа успешно обновлена.")
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Ошибка", "Ошибка формата данных в вариантах ответа.")
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Ошибка в формате числовых значений.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения: {str(e)}")

    def track_results(self):
        self.track_window = QWidget()
        self.track_window.setWindowTitle("Отслеживание результатов в реальном времени")
        layout = QVBoxLayout(self.track_window)
        layout.addWidget(QLabel("Подключенные студенты:"))
        
        for student_info in connected_students.copy():
            layout.addWidget(QLabel(student_info))
        
        self.track_window.setLayout(layout)
        self.track_window.setGeometry(460, 290, 1000, 600)
        self.track_window.show()

    def show_students_results(self):
        """Отображает результаты студентов в таблице."""
        student_results = self.db.get_student_results()
        if not student_results:
            QMessageBox.information(self, "Нет данных", "Нет данных для отображения.")
            return

        table = QTableWidget(len(student_results), 4)
        table.setHorizontalHeaderLabels(["ID", "Имя студента", "Номер лабораторной работы", "Оценка"])
    
        for i, result in enumerate(student_results):
            for j, item in enumerate(result):
                table.setItem(i, j, QTableWidgetItem(str(item)))
    
        layout = QVBoxLayout()
        layout.addWidget(table)
    
        self.results_window = QWidget()
        self.results_window.setWindowTitle("Результаты студентов")
        self.results_window.setLayout(layout)
        self.results_window.setGeometry(460, 290, 1000, 600)
        self.results_window.show()

    def update_lab_works(self):
        try:
            if not filecmp.cmp(DB_PATH, NEW_DB_PATH, shallow=False):
                reply = QMessageBox.question(
                    self, 'Обновить базу данных', 
                    "Обнаружены изменения в базе данных. Обновить базу данных?", 
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    shutil.copy(NEW_DB_PATH, DB_PATH)
                    QMessageBox.information(self, "Успех", "База данных успешно обновлена.")
                    asyncio.run(self.send_updated_db())
            else:
                QMessageBox.information(self, "Нет изменений", "Изменений в базе данных не обнаружено.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении базы данных: {str(e)}")

    async def send_updated_db(self):
        """Отправляет обновленную базу данных через WebSocket."""
        uri = "ws://localhost:5678"
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with websockets.connect(uri) as websocket:
                    with open(DB_PATH, 'rb') as f:
                        data = f.read()
                    await websocket.send(json.dumps({"type": "update_db", "data": data.decode('latin1')}))
                    await websocket.recv()
                    QMessageBox.information(self, "Успех", "Обновленная база данных отправлена устройствам.")
                    return
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось отправить базу данных: {str(e)}")

# Запуск асинхронного приложения
if __name__ == "__main__":
    asyncio.run(main())   