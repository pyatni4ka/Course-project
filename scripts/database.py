import sqlite3
import json
from typing import List, Tuple, Optional, Dict, Any

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lab_works (
                    id INTEGER PRIMARY KEY,
                    work_number INTEGER NOT NULL,
                    question_number INTEGER NOT NULL,
                    question_type TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    answer_options TEXT,
                    images TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS student_results (
                    id INTEGER PRIMARY KEY,
                    student_name TEXT NOT NULL,
                    work_number INTEGER NOT NULL,
                    grade REAL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lab_tickets (
                    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_number INTEGER NOT NULL,
                    question_type TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    question_image TEXT,
                    answer_options TEXT,
                    answer_images TEXT
                )
            ''')
        finally:
            cursor.close()
        self.conn.commit()

    def get_all_tickets(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM lab_tickets")
            tickets = cursor.fetchall()
            return [
                {
                    "ticket_id": ticket[0],
                    "work_number": ticket[1],
                    "question_type": ticket[2],
                    "question_text": ticket[3],
                    "question_image": ticket[4],
                    "answer_options": json.loads(ticket[5]) if ticket[5] else [],
                    "answer_images": json.loads(ticket[6]) if ticket[6] else []
                }
                for ticket in tickets
            ]
        finally:
            cursor.close()

    # Все остальные методы, например, add_lab_ticket, update_lab_ticket и т.д.
    # Примените аналогичное исправление в них


    def add_lab_ticket(self, theme: str, work_number: int, question_type: str, question_text: str,
                   question_image: Optional[str], answer_options: List[str],
                   answer_images: List[Optional[str]]) -> None:
        """Добавляет новый билет для лабораторной работы."""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO lab_tickets (theme, work_number, question_type, question_text, question_image, answer_options, answer_images)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (theme, work_number, question_type, question_text, question_image, json.dumps(answer_options), json.dumps(answer_images)))
        finally:
            cursor.close()
        self.conn.commit()


    def update_lab_ticket(self, ticket_id: int, theme: str, work_number: int, question_type: str, question_text: str,
                      question_image: Optional[str], answer_options: List[str],
                      answer_images: List[Optional[str]]) -> None:
        """Обновляет существующий билет лабораторной работы."""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                UPDATE lab_tickets
                SET theme = ?, work_number = ?, question_type = ?, question_text = ?, question_image = ?, 
                    answer_options = ?, answer_images = ?
                WHERE ticket_id = ?
            ''', (theme, work_number, question_type, question_text, question_image, json.dumps(answer_options), json.dumps(answer_images), ticket_id))
        finally:
            cursor.close()
        self.conn.commit()
    
    def get_lab_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о билете по его ID и возвращает словарь с данными."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM lab_tickets WHERE ticket_id = ?", (ticket_id,))
            ticket = cursor.fetchone()
            if ticket:
                return {
                    "ticket_id": ticket[0],
                    "work_number": ticket[1],
                    "question_type": ticket[2],
                    "question_text": ticket[3],
                    "question_image": ticket[4],
                    "answer_options": json.loads(ticket[5]) if ticket[5] else [],
                    "answer_images": json.loads(ticket[6]) if ticket[6] else []
                } 
        finally:
            cursor.close()
        return None

    def get_lab_works(self) -> List[Tuple[int, int, int, str, str, str]]:
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM lab_works") 
        finally:
            cursor.close()
        return cursor.fetchall()

    def get_lab_work(self, work_number: int, question_number: int) -> Optional[Tuple]:
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM lab_works WHERE work_number = ? AND question_number = ?",
                (work_number, question_number)
            )  
        finally:
            cursor.close()
        return cursor.fetchone()

    def add_lab_work(self, work_number: int, question_number: int, question_type: str,
                     question_text: str, answer_options: List[str], images: List[str]) -> None:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO lab_works (work_number, question_number, question_type, question_text, answer_options, images)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (work_number, question_number, question_type, question_text, json.dumps(answer_options), json.dumps(images)))
        finally:
            cursor.close()
        self.conn.commit()

    def update_lab_work(self, lab_work_id: int, work_number: int, question_number: int,
                        question_type: str, question_text: str, answer_options: List[str]) -> None:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                UPDATE lab_works
                SET work_number = ?, question_number = ?, question_type = ?, question_text = ?, answer_options = ?
                WHERE id = ?
            ''', (work_number, question_number, question_type, question_text, json.dumps(answer_options), lab_work_id))
        finally:
            cursor.close()
        self.conn.commit()

    def get_student_results(self) -> List[Tuple[int, str, int, float]]:
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM student_results")
        finally:
            cursor.close()
        return cursor.fetchall()

    def close(self):
        self.conn.close()
