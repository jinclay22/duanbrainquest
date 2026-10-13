# File: main_app.py
import html
import os
import random
import sqlite3
import tkinter as tk
from contextlib import closing
from tkinter import messagebox, ttk

import requests

from sound_manager import SoundManager, resource_path

DB_PATH = resource_path("brain_quest.db")
API_URL = "https://opentdb.com/api.php?amount=20&category=21&difficulty=easy&type=multiple"


class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SNLT-HP8-B3-ProjectBasic (Âm thanh)")
        self.geometry("650x500")
        self.resizable(False, False)

        self.question = None      
        self.from_api = False     
        self.score = 0
        self.sound = SoundManager()

        self._setup_ui()
        self.load_question(from_api=False)

    
    def get_db_question(self):
        try:
            with closing(sqlite3.connect(DB_PATH)) as conn:
                row = conn.execute(
                    "SELECT question_text, options_text, correct_answer_text "
                    "FROM questions ORDER BY RANDOM() LIMIT 1"
                ).fetchone()
        except sqlite3.Error as e:
            messagebox.showerror("Lỗi CSDL", str(e))
            return None
        if not row:
            return None
        q, opts, correct = row
        return {"question": q, "options": opts.split(";"), "correct": correct}

    def get_api_question(self):
        try:
            res = requests.get(API_URL, params={"amount": 1, "type": "multiple"}, timeout=10)
            res.raise_for_status()
            data = res.json()
        except requests.RequestException as e:
            messagebox.showerror("Lỗi kết nối", str(e))
            return None
        if data.get("response_code") != 0 or not data.get("results"):
            messagebox.showerror("Lỗi API", f"Code: {data.get('response_code')}")
            return None

        item = data["results"][0]
        correct = html.unescape(item["correct_answer"])
        options = [html.unescape(a) for a in item["incorrect_answers"]] + [correct]
        random.shuffle(options)
        return {"question": html.unescape(item["question"]), "options": options, "correct": correct}

    # ---------- GIAO DIỆN ----------
    def _setup_ui(self):
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(frame)
        top.pack(pady=(0, 15), fill=tk.X)
        ttk.Label(top, text="Nguồn Câu Hỏi:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(top, text="Từ CSDL Local",
                   command=lambda: self.load_question(False)).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="Từ Internet (API)",
                   command=lambda: self.load_question(True)).pack(side=tk.LEFT, padx=5)

        self.question_label = ttk.Label(frame, font=("Arial", 16, "bold"),
                                        wraplength=600, justify="center")
        self.question_label.pack(pady=20)

        options_frame = ttk.Frame(frame)
        options_frame.pack(pady=10)
        ttk.Style().configure("Option.TButton", font=("Arial", 11), padding=5)
        self.option_buttons = []
        for i in range(4):
            btn = ttk.Button(options_frame, width=30, style="Option.TButton", state=tk.DISABLED,
                             command=lambda idx=i: self.choose(idx))
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=5, sticky="ew")
            self.option_buttons.append(btn)

        self.score_label = ttk.Label(frame, text="Điểm: 0", font=("Arial", 13))
        self.score_label.pack(pady=10)
        self.feedback_label = ttk.Label(frame, font=("Arial", 12, "italic"))
        self.feedback_label.pack(pady=5)

        self.next_button = ttk.Button(frame, text="Câu Tiếp Theo", state=tk.DISABLED,
                                     command=lambda: self.load_question(self.from_api))
        self.next_button.pack(pady=15)

    def set_buttons(self, state):
        for btn in self.option_buttons:
            btn.config(state=state)

    # ---------- LOGIC CHÍNH ----------
    def load_question(self, from_api):
        self.sound.play("click")          # âm thanh khi bấm nút
        self.from_api = from_api
        self.feedback_label.config(text="")
        self.next_button.config(state=tk.DISABLED)

        if from_api:
            self.question_label.config(text="Đang tải từ API...")
            self.update_idletasks()       # vẽ lại ngay để thấy chữ "Đang tải"

        self.question = self.get_api_question() if from_api else self.get_db_question()

        if not self.question:
            self.question_label.config(text="Không tải được câu hỏi. Chọn nguồn khác.")
            self.set_buttons(tk.DISABLED)
            return

        self.question_label.config(text=self.question["question"])
        for i, btn in enumerate(self.option_buttons):
            if i < len(self.question["options"]):
                btn.config(text=self.question["options"][i], state=tk.NORMAL)
            else:
                btn.config(text="", state=tk.DISABLED)

    def choose(self, index):
        if not self.question:
            return
        self.set_buttons(tk.DISABLED)     # chặn bấm nhiều lần
        correct = self.question["correct"]

        if self.question["options"][index] == correct:
            self.score += 10
            self.feedback_label.config(text="Chính xác!", foreground="green")
            self.sound.play("correct")
        else:
            self.feedback_label.config(text=f"Sai rồi! Đáp án đúng là: {correct}", foreground="red")
            self.sound.play("wrong")

        self.score_label.config(text=f"Điểm: {self.score}")
        self.next_button.config(state=tk.NORMAL)


def init_db():
    """Tạo file DB + bảng questions nếu chưa có."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS questions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            question_text TEXT NOT NULL,
                            options_text TEXT NOT NULL,
                            correct_answer_text TEXT NOT NULL)""")
        conn.commit()


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
        print("Đã tạo CSDL. Vui lòng thêm dữ liệu mẫu vào bảng 'questions'.")
    QuizApp().mainloop()
