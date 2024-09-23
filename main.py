import sys
import sqlite3
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QMainWindow, QListWidget,
    QHBoxLayout, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QFont, QPixmap

# Функция для подключения и создания базы данных
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('students.db')
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS students
                              (surname TEXT, name TEXT, group_name TEXT, year INTEGER)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS questions
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               lab_number INTEGER,
                               question TEXT,
                               options TEXT,
                               correct_answer TEXT,
                               image BLOB)''')
        self.conn.commit()

    def find_user(self, surname, name, group_name, year):
        self.cursor.execute('SELECT * FROM students WHERE surname=? AND name=? AND group_name=? AND year=?',
                           (surname, name, group_name, year))
        return self.cursor.fetchone()

    def save_user(self, surname, name, group_name, year):
        self.cursor.execute('INSERT INTO students (surname, name, group_name, year) VALUES (?, ?, ?, ?)',
                           (surname, name, group_name, year))
        self.conn.commit()

    def load_questions(self, lab_number):
        self.cursor.execute('SELECT question, options, correct_answer, image FROM questions WHERE lab_number=?', (lab_number,))
        questions = self.cursor.fetchall()
        formatted_questions = []
        for question, options, correct_answer, image in questions:
            formatted_questions.append({
                "question": question,
                "options": options.split('|'),
                "correct_answer": correct_answer,
                "image": image
            })
        return formatted_questions

class RegistrationWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Тестирование студентов по курсу Электротехники")
        self.setGeometry(400, 150, 1000, 800)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Настроим палитру для темной темы
        self.dark_palette = QPalette()
        self.dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        self.dark_palette.setColor(QPalette.WindowText, Qt.white)
        self.dark_palette.setColor(QPalette.Base, QColor(40, 40, 40))
        self.dark_palette.setColor(QPalette.Text, Qt.white)
        self.dark_palette.setColor(QPalette.Button, QColor(70, 70, 70))
        self.dark_palette.setColor(QPalette.ButtonText, Qt.white)

        self.setPalette(self.dark_palette)

        self.create_input_field(layout, "Фамилия:", "surname_input")
        self.create_input_field(layout, "Имя:", "name_input")
        self.create_input_field(layout, "Группа:", "group_input")
        self.create_input_field(layout, "Год:", "year_input")

        # Кнопка "Далее"
        self.next_button = QPushButton("Далее")
        self.next_button.clicked.connect(self.save_or_login_user)
        layout.addWidget(self.next_button)

        # Кнопка переключения темы
        self.theme_button = QPushButton("Темная тема")
        self.theme_button.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_button)

        self.setLayout(layout)
        self.is_dark_theme = True

    def create_input_field(self, layout, label_text, object_name):
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignLeft)
        input_field = QLineEdit()
        input_field.setObjectName(object_name)
        input_field.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        layout.addWidget(input_field)

    def toggle_theme(self):
        if self.is_dark_theme:
            self.theme_button.setText("Светлая тема")
            self.setPalette(self.dark_palette)
        else:
            light_palette = QPalette()
            light_palette.setColor(QPalette.Window, QColor(255, 255, 255))
            light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
            self.setPalette(light_palette)
            self.theme_button.setText("Темная тема")

        self.is_dark_theme = not self.is_dark_theme

    def save_or_login_user(self):
        surname = self.findChild(QLineEdit, "surname_input").text()
        name = self.findChild(QLineEdit, "name_input").text()
        group_name = self.findChild(QLineEdit, "group_input").text()
        year = self.findChild(QLineEdit, "year_input").text()

        if not all([surname, name, group_name, year]):
            return

        user = self.db.find_user(surname, name, group_name, year)
        if not user:
            self.db.save_user(surname, name, group_name, year)

        self.hide()
        self.lab_window = LabWindow(surname, name, group_name, year, self.db)
        self.lab_window.show()

class LabWindow(QMainWindow):
    def __init__(self, surname, name, group_name, year, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Лабораторные работы")
        self.setGeometry(400, 150, 1000, 800)

        layout = QVBoxLayout()

        self.lab_list = QListWidget()
        self.lab_list.addItems([
            "Лабораторная работа 1",
            "Лабораторная работа 2",
            "Лабораторная работа 3",
            "Лабораторная работа 4",
            "Лабораторная работа 5"
        ])
        layout.addWidget(self.lab_list)

        user_info = QLabel(f"{surname} {name}, Группа: {group_name}, Год: {year}")
        user_info.setAlignment(Qt.AlignRight)
        layout.addWidget(user_info)

        self.next_button = QPushButton("Далее")
        self.next_button.clicked.connect(self.handle_next_button)
        layout.addWidget(self.next_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def handle_next_button(self):
        selected_lab = self.lab_list.currentItem()
        if selected_lab:
            selected_lab_text = selected_lab.text().split()[-1]
            self.lab_work_window = LabWorkWindow(selected_lab_text, self.db)
            self.lab_work_window.show()
            self.close()

class LabWorkWindow(QWidget):
    def __init__(self, lab_number, db):
        super().__init__()
        self.db = db
        self.setWindowTitle(f"Лабораторная работа {lab_number}")
        self.setGeometry(400, 150, 1000, 800)

        self.lab_number = int(lab_number)
        self.questions = self.db.load_questions(self.lab_number)

        self.current_question = 0
        self.selected_answers = [None] * len(self.questions)

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.image_label)

        self.question_label = QLabel(self)
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setFont(QFont("Arial", 16))
        self.layout.addWidget(self.question_label)

        self.radio_group = QButtonGroup(self)
        self.radio_layout = QVBoxLayout()
        self.layout.addLayout(self.radio_layout)

        self.nav_layout = QHBoxLayout()

        self.prev_button = QPushButton("<")
        self.prev_button.clicked.connect(self.prev_question)
        self.nav_layout.addWidget(self.prev_button)

        self.next_button = QPushButton(">")
        self.next_button.clicked.connect(self.next_question)
        self.nav_layout.addWidget(self.next_button)

        self.layout.addLayout(self.nav_layout)
        self.setLayout(self.layout)

        self.load_question(self.current_question)

    def load_question(self, index):
        question_data = self.questions[index]
        self.question_label.setText(question_data['question'])

        pixmap = QPixmap()
        pixmap.loadFromData(question_data['image'])
        self.image_label.setPixmap(pixmap.scaled(400, 300, Qt.KeepAspectRatio))

        for i in reversed(range(self.radio_layout.count())):
            widget = self.radio_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.radio_buttons = []
        self.radio_group = QButtonGroup(self)
        for option in question_data['options']:
            radio_btn = QRadioButton(option)
            self.radio_group.addButton(radio_btn)
            self.radio_layout.addWidget(radio_btn)
            self.radio_buttons.append(radio_btn)

        if self.selected_answers[index] is not None:
            self.radio_buttons[self.selected_answers[index]].setChecked(True)

    def prev_question(self):
        if self.current_question > 0:
            self.selected_answers[self.current_question] = self.get_selected_answer()
            self.current_question -= 1
            self.load_question(self.current_question)

    def next_question(self):
        if self.current_question < len(self.questions) - 1:
            self.selected_answers[self.current_question] = self.get_selected_answer()
            self.current_question += 1
            self.load_question(self.current_question)
        else:
            self.selected_answers[self.current_question] = self.get_selected_answer()
            self.show_results()

    def get_selected_answer(self):
        for i, button in enumerate(self.radio_buttons):
            if button.isChecked():
                return i
        return None

    def show_results(self):
        score = sum(
            1 for i, answer in enumerate(self.selected_answers)
            if answer == self.questions[i]['options'].index(self.questions[i]['correct_answer'])
        )
        QMessageBox.information(self, "Результаты", f"Ваш результат: {score} из {len(self.questions)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = Database()
    registration_window = RegistrationWindow(db)
    registration_window.show()
    sys.exit(app.exec())
