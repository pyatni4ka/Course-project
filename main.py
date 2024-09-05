import sys
import os
import sqlite3
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QLabel, QRadioButton, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QButtonGroup

class TestApp(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Тестирование студентов")
        self.setGeometry(100, 100, 800, 600)

        self.database_path = "database"
        self.css_path = "css/styles.css"
        
        self.questions = [
            {"image": os.path.join(self.database_path, "image1.jpg"), "question": "Что изображено на картинке?", "options": ["Кошка", "Собака", "Птица"], "answer": "Кошка"},
            {"image": os.path.join(self.database_path, "image2.jpg"), "question": "Что изображено на картинке?", "options": ["Автомобиль", "Самолет", "Корабль"], "answer": "Автомобиль"},
            {"image": os.path.join(self.database_path, "image3.jpg"), "question": "Что изображено на картинке?", "options": ["Папа", "НеПапа", "Кто"], "answer": "Папа"},
        ]

        self.current_question = 0
        self.selected_answers = [None] * len(self.questions)

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        # Top layout for the finish button
        self.top_layout = QHBoxLayout()
        self.finish_button = QPushButton("Завершить тест", self)
        self.finish_button.setFont(QtGui.QFont("Arial", 14))
        self.finish_button.clicked.connect(self.finish_test)
        self.finish_button.setVisible(False)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.finish_button)
        self.layout.addLayout(self.top_layout)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.image_label)

        self.question_label = QLabel(self)
        self.question_label.setAlignment(QtCore.Qt.AlignCenter)
        self.question_label.setFont(QtGui.QFont("Arial", 16))
        self.layout.addWidget(self.question_label)

        self.radio_group = QButtonGroup(self)
        self.radio_layout = QVBoxLayout()
        self.layout.addLayout(self.radio_layout)

        self.nav_layout = QHBoxLayout()
        self.nav_layout.setAlignment(QtCore.Qt.AlignCenter)

        self.prev_button = QPushButton("<", self)
        self.prev_button.setFixedSize(80, 50)
        self.prev_button.setFont(QtGui.QFont("Arial", 14))
        self.prev_button.setStyleSheet("border-radius: 25px;")
        self.prev_button.clicked.connect(self.prev_question)
        self.nav_layout.addWidget(self.prev_button)

        self.nav_buttons = []
        for i in range(len(self.questions)):
            btn = QPushButton(str(i + 1), self)
            btn.setFixedSize(50, 50)
            btn.setFont(QtGui.QFont("Arial", 14))
            btn.setStyleSheet("border-radius: 25px;")
            btn.clicked.connect(lambda checked, idx=i: self.navigate_to_question(idx))
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.nav_buttons.append(btn)
            self.nav_layout.addWidget(btn)

        self.next_button = QPushButton(">", self)
        self.next_button.setFixedSize(80, 50)
        self.next_button.setFont(QtGui.QFont("Arial", 14))
        self.next_button.setStyleSheet("border-radius: 25px;")
        self.next_button.clicked.connect(self.next_question)
        self.nav_layout.addWidget(self.next_button)

        self.layout.addLayout(self.nav_layout)

        self.setLayout(self.layout)

        self.load_stylesheet()
        self.load_question(self.current_question)

    def load_stylesheet(self):
        if os.path.exists(self.css_path):
            with open(self.css_path, "r") as f:
                self.setStyleSheet(f.read())

    def load_question(self, index):
        self.current_question = index

        image_path = self.questions[self.current_question]["image"]
        if os.path.exists(image_path):
            pixmap = QtGui.QPixmap(image_path)
            self.image_label.setPixmap(pixmap.scaled(self.width(), int(self.height() * 0.5), QtCore.Qt.KeepAspectRatio))
        else:
            self.image_label.setText("Изображение не найдено")

        self.question_label.setText(self.questions[self.current_question]["question"])

        # Очистка предыдущих радиокнопок
        for i in reversed(range(self.radio_layout.count())): 
            widget = self.radio_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        self.radio_buttons = []
        self.radio_group = QButtonGroup(self)

        for option in self.questions[self.current_question]["options"]:
            radio_btn = QRadioButton(option, self)
            radio_btn.setFont(QtGui.QFont("Arial", 14))
            radio_btn.toggled.connect(self.check_all_answers_selected)
            self.radio_buttons.append(radio_btn)
            self.radio_group.addButton(radio_btn)
            self.radio_layout.addWidget(radio_btn)

        if self.selected_answers[self.current_question] is not None:
            for btn in self.radio_buttons:
                if btn.text() == self.selected_answers[self.current_question]:
                    btn.setChecked(True)

        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.prev_button.setVisible(self.current_question > 0)
        self.next_button.setVisible(self.current_question < len(self.questions) - 1)

    def prev_question(self):
        self.save_answer()
        if self.current_question > 0:
            self.load_question(self.current_question - 1)

    def next_question(self):
        self.save_answer()
        if self.current_question < len(self.questions) - 1:
            self.load_question(self.current_question + 1)

    def navigate_to_question(self, index):
        self.save_answer()
        self.load_question(index)

    def save_answer(self):
        selected_button = self.radio_group.checkedButton()
        if selected_button:
            self.selected_answers[self.current_question] = selected_button.text()

    def check_all_answers_selected(self):
        self.save_answer()
        if all(answer is not None for answer in self.selected_answers):
            self.finish_button.setVisible(True)

    def save_to_database(self, question, answer):
        db_path = os.path.join(self.database_path, 'test_results.db')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT
            )
        ''')

        cursor.execute('INSERT INTO results (question, answer) VALUES (?, ?)', (question, answer))

        conn.commit()
        conn.close()

    def finish_test(self):
        self.save_answer()
        for question_data, answer in zip(self.questions, self.selected_answers):
            self.save_to_database(question_data['question'], answer)
        self.show_results()

    def show_results(self):
        results = []
        for i, question_data in enumerate(self.questions):
            correct_answer = question_data['answer']
            selected_answer = self.selected_answers[i]
            result = f"Вопрос: {question_data['question']}\nВаш ответ: {selected_answer}\nПравильный ответ: {correct_answer}\n"
            results.append(result)
        
        QtWidgets.QMessageBox.information(self, "Результаты теста", "\n\n".join(results))

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = TestApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
