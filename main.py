# main.py (Modified - 10 Questions per Level)

import tkinter as tk
from tkinter import messagebox, simpledialog, font, scrolledtext # Import scrolledtext
import random
import time
import os

SCORE_FILE = "scores.txt"
TOTAL_QUESTIONS = 10 # <<< MODIFIED: Changed from 5 to 10 questions per game
FEEDBACK_DELAY_MS = 1200 # Delay for feedback visibility
RETRY_FEEDBACK_DELAY_MS = 1700 # Slightly longer delay after retry/skip/timeout

# ========== Color Palette (from Untitled-1.py) ==========
COLOR_BACKGROUND = "#F0F8FF"
COLOR_FRAME_BG = "#F0F8FF"
COLOR_TEXT = "#333333"
COLOR_TITLE = "#4682B4"
COLOR_BUTTON = "#B0E0E6"      # General button
COLOR_BUTTON_TEXT = "#2F4F4F"
COLOR_BUTTON_HOVER = "#ADD8E6"
COLOR_QUIT = "#CD5C5C"
COLOR_QUIT_TEXT = "#FFFFFF"
COLOR_QUIT_HOVER = "#F08080"
COLOR_ENTRY_BG = "#FFFFFF"
COLOR_ENTRY_FG = "#333333"
COLOR_CORRECT = "#2E8B57"
COLOR_WRONG = "#DC143C"
COLOR_WARNING = "#DAA520" # For timeout/invalid/retry offer
COLOR_TIMER = "#1E90FF"
COLOR_LEADERBOARD_BG = "#FAF0E6"
COLOR_SUMMARY_BG = "#FAF0E6" # Reusing for summary/leaderboard

# Difficulty Button Colors
COLOR_EASY = "#98FB98"
COLOR_MEDIUM = "#FFDAB9"
COLOR_HARD = "#FFB6C1"
COLOR_RANDOM = "#B0C4DE"

# Action Button Colors
COLOR_SUBMIT = "#5F9EA0"      # Cadet Blue for Submit/Play Again
COLOR_SUBMIT_TEXT = "#FFFFFF"
COLOR_SUBMIT_HOVER = "#66CDAA"
COLOR_RETRY = "#FFA07A"      # Light Salmon (Soft Orange/Pink)
COLOR_RETRY_TEXT = "#FFFFFF"
COLOR_RETRY_HOVER = "#FA8072"  # Salmon
COLOR_SKIP = "#D3D3D3"      # Light Gray
COLOR_SKIP_TEXT = "#696969"   # Dim Gray
COLOR_SKIP_HOVER = "#C0C0C0"  # Silver

# ========== Non-GUI Logic (Adapted for Difficulty Modes) ==========

def get_time_limit(difficulty_mode, question_index):
    """Calculates the time limit in seconds based on difficulty mode and question progress."""
    if difficulty_mode == "easy":
        base_time = 40
        time_reduction_per_q = 1.5
        min_time = 20
    elif difficulty_mode == "medium":
        base_time = 30
        time_reduction_per_q = 1.5
        min_time = 15
    elif difficulty_mode == "hard":
        base_time = 25
        time_reduction_per_q = 1.5
        min_time = 10
    else: # Default to medium
        base_time = 30
        time_reduction_per_q = 1.5
        min_time = 15
    # Adjust time reduction based on TOTAL_QUESTIONS to ensure it doesn't drop too fast
    # Example: Scale reduction based on total questions (optional, but can be smoother)
    # time_reduction_per_q = time_reduction_per_q * (5 / TOTAL_QUESTIONS) # Scale reduction if needed
    time_limit = base_time - (question_index - 1) * time_reduction_per_q
    return max(min_time, int(time_limit))

def generate_question_data(difficulty_mode):
    """Generates question components based on the chosen difficulty mode."""
    if difficulty_mode == "random":
        actual_difficulty = random.choice(["easy", "medium", "hard"])
    else:
        actual_difficulty = difficulty_mode

    if actual_difficulty == "easy":
        num1, num2 = random.randint(1, 15), random.randint(1, 10)
        op = random.choice(['+', '-'])
        if op == '-' and num1 < num2: num1, num2 = num2, num1
    elif actual_difficulty == "medium":
        num1, num2 = random.randint(10, 50), random.randint(5, 30)
        op = random.choice(['+', '-', '*'])
        if op == '*': num1, num2 = random.randint(2, 12), random.randint(2, 10)
    elif actual_difficulty == "hard":
        num1, num2 = random.randint(20, 100), random.randint(10, 70)
        op = random.choice(['+', '-', '*'])
        if op == '*': num1, num2 = random.randint(5, 20), random.randint(5, 15)
    else: # Fallback
        print(f"Warning: Unknown difficulty '{actual_difficulty}', defaulting to easy.")
        actual_difficulty = "easy"
        num1, num2, op = 5, 3, '+'

    question_str = f"{num1} {op} {num2}"
    try:
        answer = eval(question_str)
    except Exception as e:
        print(f"Error evaluating question '{question_str}': {e}")
        return "Error", 0, actual_difficulty
    return question_str, answer, actual_difficulty

def save_score(name, score, mode):
    """Appends score to the score file in 'Name,Score/Total (Mode)' format."""
    try:
        with open(SCORE_FILE, "a") as f:
            f.write(f"{name},{score}/{TOTAL_QUESTIONS} ({mode.capitalize()})\n")
    except IOError as e:
        messagebox.showerror("File Error", f"Error saving score: {e}")

def load_scores():
    """Loads scores, handling 'Score/Total (Mode)' format. Returns list of (name, score_value, score_str)."""
    scores = []
    if not os.path.exists(SCORE_FILE): return scores
    try:
        with open(SCORE_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                try:
                    name, score_part = line.strip().split(",", 1)
                    score_part = score_part.strip()
                    if '/' in score_part:
                        score_val_str = score_part.split('/')[0]
                        score_value = int(score_val_str)
                        # Optional: Could also extract total from score_part if needed for validation
                    else: # Handle older format or lines without '/'
                        score_value = int(score_part.split(' ')[0])
                    scores.append((name, score_value, score_part))
                except (ValueError, IndexError) as e:
                    print(f"Skipping malformed score line: {line.strip()} ({e})")
                    continue
    except IOError as e:
        messagebox.showerror("File Error", f"Error reading score file: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred loading scores: {e}")
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores

# ========== GUI Application Class ==========

class MindMathGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 MindMath - Brain Trainer ✨")
        self.root.geometry("550x750") # Increased height for summary
        self.root.configure(bg=COLOR_BACKGROUND)

        # --- Fonts ---
        self.title_font = font.Font(family="Arial", size=22, weight="bold")
        self.label_font = font.Font(family="Arial", size=12)
        self.button_font = font.Font(family="Arial", size=11, weight="bold")
        self.question_font = font.Font(family="Arial", size=18, weight="bold")
        self.feedback_font = font.Font(family="Arial", size=13, weight="bold")
        self.summary_font = font.Font(family="Consolas", size=10) # Monospaced for table
        self.leaderboard_font = font.Font(family="Consolas", size=10)

        # --- Game State Variables ---
        self.player_name = "Player"
        self.score = 0
        self.streak = 0
        self.current_question_index = 0
        self.difficulty_mode = None
        self.correct_answer = None
        self.question_start_time = 0
        self.current_time_limit = 0
        self.timer_id = None
        self.actual_difficulty_for_random = None
        self.current_question_str = "" # Store question for history
        self.game_history = [] # List to store results for summary
        self.is_retry_attempt = False # Flag for retry state

        # --- Widgets ---
        self.start_frame = tk.Frame(root, bg=COLOR_FRAME_BG)
        self.game_frame = tk.Frame(root, bg=COLOR_FRAME_BG)
        self.end_frame = tk.Frame(root, bg=COLOR_FRAME_BG)

        self._create_start_widgets()
        self._create_game_widgets()
        self._create_end_widgets()

        self.show_frame(self.start_frame)

    # --- Screen Management ---
    def show_frame(self, frame_to_show):
        self.start_frame.pack_forget()
        self.game_frame.pack_forget()
        self.end_frame.pack_forget()
        frame_to_show.pack(fill="both", expand=True, padx=30, pady=30)

    # --- Widget Creation ---
    def _create_start_widgets(self):
        tk.Label(self.start_frame, text="Welcome to MindMath!", font=self.title_font, bg=COLOR_FRAME_BG, fg=COLOR_TITLE).pack(pady=(10, 25))
        tk.Label(self.start_frame, text="Enter your name:", font=self.label_font, bg=COLOR_FRAME_BG, fg=COLOR_TEXT).pack(pady=5)
        self.name_entry = tk.Entry(self.start_frame, font=self.label_font, width=25, bg=COLOR_ENTRY_BG, fg=COLOR_ENTRY_FG, relief="solid", borderwidth=1, justify='center')
        self.name_entry.pack(pady=(0, 15))
        self.name_entry.insert(0, "Player")

        tk.Label(self.start_frame, text="Choose Difficulty:", font=self.label_font, bg=COLOR_FRAME_BG, fg=COLOR_TEXT).pack(pady=(15, 10))
        difficulty_frame = tk.Frame(self.start_frame, bg=COLOR_FRAME_BG)
        difficulty_frame.pack(pady=5)
        button_opts = {'font': self.button_font, 'width': 12, 'pady': 5, 'relief': "raised", 'borderwidth': 2}
        hover_opts = {'activebackground': COLOR_BUTTON_HOVER, 'activeforeground': COLOR_BUTTON_TEXT}
        tk.Button(difficulty_frame, text="Easy 🌱", command=lambda: self.set_difficulty_and_start("easy"), bg=COLOR_EASY, fg=COLOR_BUTTON_TEXT, **button_opts, **hover_opts).grid(row=0, column=0, padx=10, pady=8)
        tk.Button(difficulty_frame, text="Medium 🔥", command=lambda: self.set_difficulty_and_start("medium"), bg=COLOR_MEDIUM, fg=COLOR_BUTTON_TEXT, **button_opts, **hover_opts).grid(row=0, column=1, padx=10, pady=8)
        tk.Button(difficulty_frame, text="Hard 🚀", command=lambda: self.set_difficulty_and_start("hard"), bg=COLOR_HARD, fg=COLOR_BUTTON_TEXT, **button_opts, **hover_opts).grid(row=1, column=0, padx=10, pady=8)
        tk.Button(difficulty_frame, text="Random ✨", command=lambda: self.set_difficulty_and_start("random"), bg=COLOR_RANDOM, fg=COLOR_BUTTON_TEXT, **button_opts, **hover_opts).grid(row=1, column=1, padx=10, pady=8)

        tk.Frame(self.start_frame, height=30, bg=COLOR_FRAME_BG).pack() # Spacer
        tk.Button(self.start_frame, text="🏆 Show Leaderboard", font=self.button_font, command=self.show_leaderboard_popup, width=20, pady=5, bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT, activebackground=COLOR_BUTTON_HOVER, activeforeground=COLOR_BUTTON_TEXT, relief="raised", borderwidth=2).pack(pady=8)
        tk.Button(self.start_frame, text="❌ Quit Game", font=self.button_font, command=self.root.quit, width=20, pady=5, bg=COLOR_QUIT, fg=COLOR_QUIT_TEXT, activebackground=COLOR_QUIT_HOVER, activeforeground=COLOR_QUIT_TEXT, relief="raised", borderwidth=2).pack(pady=8)

    def _create_game_widgets(self):
        top_frame = tk.Frame(self.game_frame, bg=COLOR_FRAME_BG)
        top_frame.pack(fill='x', pady=(5, 15))
        self.progress_label = tk.Label(top_frame, text="", font=self.label_font, bg=COLOR_FRAME_BG, fg=COLOR_TEXT)
        self.progress_label.pack(side=tk.LEFT, padx=10)
        self.mode_label = tk.Label(top_frame, text="", font=self.label_font, bg=COLOR_FRAME_BG, fg=COLOR_TEXT)
        self.mode_label.pack(side=tk.LEFT, expand=True)
        self.timer_label = tk.Label(top_frame, text="", fg=COLOR_TIMER, bg=COLOR_FRAME_BG, font=('Arial', 12, 'bold'))
        self.timer_label.pack(side=tk.RIGHT, padx=10)

        self.question_label = tk.Label(self.game_frame, text="Question appears here", font=self.question_font, bg=COLOR_FRAME_BG, fg=COLOR_TITLE, wraplength=450)
        self.question_label.pack(pady=25) # Reduced padding
        self.answer_entry = tk.Entry(self.game_frame, font=self.label_font, width=18, bg=COLOR_ENTRY_BG, fg=COLOR_ENTRY_FG, relief="solid", borderwidth=1, justify='center')
        self.answer_entry.pack(pady=15)
        self.answer_entry.bind("<Return>", self.submit_answer_event)

        # Submit Button (initially visible)
        self.submit_button = tk.Button(self.game_frame, text="Submit ✅", font=self.button_font, command=self.submit_answer, width=15, pady=5, bg=COLOR_SUBMIT, fg=COLOR_SUBMIT_TEXT, activebackground=COLOR_SUBMIT_HOVER, activeforeground=COLOR_SUBMIT_TEXT, relief="raised", borderwidth=2)
        self.submit_button.pack(pady=10)

        # Retry/Skip Frame (initially hidden)
        self.retry_frame = tk.Frame(self.game_frame, bg=COLOR_FRAME_BG)
        # We will .pack() this frame only when needed
        retry_opts = {'font': self.button_font, 'width': 12, 'pady': 5, 'relief': "raised", 'borderwidth': 2}
        self.retry_button = tk.Button(self.retry_frame, text="Retry 🤔", command=self.handle_retry, bg=COLOR_RETRY, fg=COLOR_RETRY_TEXT, activebackground=COLOR_RETRY_HOVER, activeforeground=COLOR_RETRY_TEXT, **retry_opts)
        self.retry_button.grid(row=0, column=0, padx=8)
        self.skip_button = tk.Button(self.retry_frame, text="Skip ⏩", command=self.skip_retry, bg=COLOR_SKIP, fg=COLOR_SKIP_TEXT, activebackground=COLOR_SKIP_HOVER, activeforeground=COLOR_SKIP_TEXT, **retry_opts)
        self.skip_button.grid(row=0, column=1, padx=8)

        self.feedback_label = tk.Label(self.game_frame, text="", font=self.feedback_font, bg=COLOR_FRAME_BG, height=2, wraplength=450)
        self.feedback_label.pack(pady=15) # Reduced padding

    def _create_end_widgets(self):
        tk.Label(self.end_frame, text="🎯 Quiz Over! 🎯", font=self.title_font, bg=COLOR_FRAME_BG, fg=COLOR_TITLE).pack(pady=(10, 10))
        self.mode_played_label = tk.Label(self.end_frame, text="Mode Played: ", font=self.label_font, bg=COLOR_FRAME_BG, fg=COLOR_TEXT)
        self.mode_played_label.pack(pady=3)
        self.final_score_label = tk.Label(self.end_frame, text=f"Your final score: 0/{TOTAL_QUESTIONS}", bg=COLOR_FRAME_BG, fg=COLOR_TEXT, font=('Arial', 14, 'bold'))
        self.final_score_label.pack(pady=(3, 15))

        # --- Game Summary Section ---
        tk.Label(self.end_frame, text="📊 Game Summary:", font=self.label_font, bg=COLOR_FRAME_BG, fg=COLOR_TEXT).pack(pady=(10, 5))
        # <<< MODIFIED: Increased height slightly for more questions
        self.summary_text = scrolledtext.ScrolledText(self.end_frame, height=12, width=65, font=self.summary_font, relief="solid", borderwidth=1, bg=COLOR_SUMMARY_BG, fg=COLOR_TEXT, wrap=tk.WORD)
        self.summary_text.pack(pady=5)
        self.summary_text.config(state=tk.DISABLED)
        # --- End Game Summary Section ---

        tk.Label(self.end_frame, text="🏆 Leaderboard (Top 5):", font=self.label_font, bg=COLOR_FRAME_BG, fg=COLOR_TEXT).pack(pady=(15, 5))
        self.leaderboard_text = scrolledtext.ScrolledText(self.end_frame, height=7, width=65, font=self.leaderboard_font, relief="solid", borderwidth=1, bg=COLOR_LEADERBOARD_BG, fg=COLOR_TEXT, wrap=tk.NONE) # Changed to ScrolledText
        self.leaderboard_text.pack(pady=5)
        self.leaderboard_text.config(state=tk.DISABLED)

        button_frame = tk.Frame(self.end_frame, bg=COLOR_FRAME_BG)
        button_frame.pack(pady=20) # Reduced padding
        tk.Button(button_frame, text="Play Again 🔁", font=self.button_font, command=self.play_again, width=18, pady=5, bg=COLOR_SUBMIT, fg=COLOR_SUBMIT_TEXT, activebackground=COLOR_SUBMIT_HOVER, activeforeground=COLOR_SUBMIT_TEXT, relief="raised", borderwidth=2).grid(row=0, column=0, padx=15)
        tk.Button(button_frame, text="Quit Game ❌", font=self.button_font, command=self.root.quit, width=18, pady=5, bg=COLOR_QUIT, fg=COLOR_QUIT_TEXT, activebackground=COLOR_QUIT_HOVER, activeforeground=COLOR_QUIT_TEXT, relief="raised", borderwidth=2).grid(row=0, column=1, padx=15)

    # --- Game Logic Methods ---

    def set_difficulty_and_start(self, mode):
        """Sets the chosen difficulty and starts the game."""
        name = self.name_entry.get().strip()
        self.player_name = name if name else "Player"
        self.difficulty_mode = mode
        self.score = 0
        self.streak = 0
        self.current_question_index = 0
        self.game_history = [] # Reset history for new game
        self.is_retry_attempt = False # Ensure reset
        self.mode_label.config(text=f"Mode: {self.difficulty_mode.capitalize()}")
        self.show_frame(self.game_frame)
        self.next_question()

    def next_question(self):
        # Reset UI for new question
        self.is_retry_attempt = False # Ensure retry flag is off
        self.timer_label.config(text="")
        self.feedback_label.config(text="", fg=COLOR_TEXT)
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.config(state=tk.NORMAL)
        self.submit_button.pack(pady=10) # Ensure submit is visible
        self.submit_button.config(state=tk.NORMAL)
        self.retry_frame.pack_forget() # Ensure retry/skip is hidden

        if self.current_question_index >= TOTAL_QUESTIONS:
            self.end_game()
            return

        self.current_question_index += 1

        # Generate question data
        question_str, self.correct_answer, self.actual_difficulty_for_random = generate_question_data(self.difficulty_mode)
        self.current_question_str = question_str # Store for history

        if question_str == "Error":
             messagebox.showerror("Error", "Could not generate question. Skipping.")
             self.record_history("N/A", "Error") # Record error in history
             self.root.after(100, self.next_question)
             return

        # Get dynamic time limit
        difficulty_for_timer = self.difficulty_mode if self.difficulty_mode != "random" else self.actual_difficulty_for_random
        self.current_time_limit = get_time_limit(difficulty_for_timer, self.current_question_index)

        # Update UI labels
        self.progress_label.config(text=f"Q: {self.current_question_index}/{TOTAL_QUESTIONS}")
        mode_display = self.difficulty_mode.capitalize()
        if self.difficulty_mode == "random":
             mode_display = f"Random ({self.actual_difficulty_for_random.capitalize()})"
        self.mode_label.config(text=f"Mode: {mode_display}")
        self.question_label.config(text=f"🧮 Solve: {question_str} = ?")

        self.answer_entry.focus_set()
        self.question_start_time = time.time()
        self.update_timer()

        # Start timer
        if self.timer_id: self.root.after_cancel(self.timer_id)
        self.timer_id = self.root.after(self.current_time_limit * 1000, self.timeout)

    def update_timer(self):
        if not self.game_frame.winfo_ismapped() or (self.answer_entry.cget('state') == tk.DISABLED and self.timer_label.cget('text') != "⏱ Time's Up!"):
             if self.timer_label.cget('text') != "⏱ Time's Up!": self.timer_label.config(text="")
             return
        elapsed = time.time() - self.question_start_time
        remaining = max(0, self.current_time_limit - int(elapsed))
        self.timer_label.config(text=f"⏱ {remaining}s")
        if remaining > 0 and (self.answer_entry.cget('state') == tk.NORMAL or self.retry_frame.winfo_ismapped()): # Check retry frame too
             self.root.after(1000, self.update_timer)

    def timeout(self):
        if not self.game_frame.winfo_ismapped() or (self.answer_entry.cget('state') == tk.DISABLED and not self.retry_frame.winfo_ismapped()):
            return
        if self.timer_id: self.root.after_cancel(self.timer_id); self.timer_id = None

        self.feedback_label.config(text=f"⏱ Time's up! Answer was: {self.correct_answer}", fg=COLOR_WARNING)
        self.streak = 0
        self.answer_entry.config(state=tk.DISABLED)
        self.submit_button.pack_forget() # Hide submit
        self.retry_frame.pack_forget() # Hide retry/skip
        self.timer_label.config(text="⏱ Time's Up!")
        self.is_retry_attempt = False # Cannot retry timeout

        self.record_history("Timeout", "Timeout") # Record timeout
        self.root.after(RETRY_FEEDBACK_DELAY_MS, self.next_question) # Use longer delay

    def submit_answer_event(self, event):
        if self.submit_button.winfo_ismapped() and self.submit_button.cget('state') == tk.NORMAL:
            self.submit_answer()

    def submit_answer(self):
        if self.timer_id: self.root.after_cancel(self.timer_id); self.timer_id = None
        self.timer_label.config(text="")
        self.answer_entry.config(state=tk.DISABLED)
        self.submit_button.config(state=tk.DISABLED) # Disable submit during processing

        user_answer_str = self.answer_entry.get().strip()
        final_result_str = ""

        try:
            if not user_answer_str:
                 self.feedback_label.config(text="❌ Please enter an answer.", fg=COLOR_WRONG)
                 self.streak = 0
                 final_result_str = "Invalid (Empty)"
                 self.record_history(user_answer_str, final_result_str)
                 self.root.after(FEEDBACK_DELAY_MS, self.next_question)
                 return

            user_answer = int(user_answer_str)

            if user_answer == self.correct_answer:
                if self.is_retry_attempt:
                    self.feedback_label.config(text=f"✅ Correct on Retry! 😎", fg=COLOR_CORRECT)
                    final_result_str = "Correct (Retry)"
                    # No score/streak increase on retry
                else:
                    self.feedback_label.config(text="✅ Correct! Great job! ✨", fg=COLOR_CORRECT)
                    self.score += 1
                    self.streak += 1
                    final_result_str = "Correct"
                self.record_history(user_answer_str, final_result_str)
                self.is_retry_attempt = False # Reset flag
                self.root.after(FEEDBACK_DELAY_MS, self.next_question)

            else: # Wrong Answer
                self.streak = 0
                if self.is_retry_attempt: # Failed the retry
                    self.feedback_label.config(text=f"❌ Still incorrect. Answer was: {self.correct_answer}", fg=COLOR_WRONG)
                    final_result_str = "Wrong (Retry Failed)"
                    self.record_history(user_answer_str, final_result_str)
                    self.is_retry_attempt = False
                    self.submit_button.pack_forget() # Hide submit after failed retry
                    self.root.after(RETRY_FEEDBACK_DELAY_MS, self.next_question)
                else: # First wrong answer - Offer Retry
                    self.feedback_label.config(text="❌ Oops! Not quite. Try again?", fg=COLOR_WARNING)
                    # Don't record history yet, wait for retry/skip outcome
                    self.submit_button.pack_forget() # Hide Submit
                    self.retry_frame.pack(pady=10) # Show Retry/Skip

        except ValueError:
            self.feedback_label.config(text="❌ Invalid input! Enter numbers only.", fg=COLOR_WRONG)
            self.streak = 0
            final_result_str = "Invalid (Non-numeric)"
            self.record_history(user_answer_str, final_result_str)
            self.is_retry_attempt = False # Cannot retry invalid input
            self.root.after(FEEDBACK_DELAY_MS, self.next_question)

    # --- Retry/Skip Handlers ---
    def handle_retry(self):
        self.is_retry_attempt = True
        self.retry_frame.pack_forget() # Hide retry/skip
        self.submit_button.pack(pady=10) # Show submit again
        self.submit_button.config(state=tk.NORMAL)
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.config(state=tk.NORMAL)
        self.feedback_label.config(text="Okay, take another shot:", fg=COLOR_TEXT) # Neutral feedback
        self.answer_entry.focus_set()
        # Timer does not restart

    def skip_retry(self):
        self.retry_frame.pack_forget() # Hide retry/skip
        self.feedback_label.config(text=f"❌ Skipped. Answer was: {self.correct_answer}", fg=COLOR_WRONG)
        self.record_history("Skipped", "Wrong (Skipped)") # Record skip
        self.is_retry_attempt = False
        self.root.after(RETRY_FEEDBACK_DELAY_MS, self.next_question) # Longer delay

    # --- History and Summary ---
    def record_history(self, user_answer_display, result):
        """Adds the details of the completed question to the game history."""
        history_entry = {
            "question": self.current_question_str,
            "user_answer": user_answer_display, # Store string representation
            "correct_answer": self.correct_answer,
            "result": result # e.g., "Correct", "Wrong (Retry Failed)", "Timeout"
        }
        self.game_history.append(history_entry)

    def display_game_summary(self, text_widget):
        """Formats and displays the game history in the summary Text widget."""
        text_widget.config(state=tk.NORMAL)
        text_widget.delete('1.0', tk.END)

        if not self.game_history:
            text_widget.insert(tk.END, "No game history recorded.")
        else:
            q_width, ua_width, ca_width, r_width = 18, 18, 12, 22
            total_width = q_width + ua_width + ca_width + r_width + 3
            header = f"{'Question':<{q_width}} {'Your Answer':<{ua_width}} {'Correct':<{ca_width}} {'Result':<{r_width}}\n"
            separator = "=" * total_width + "\n"
            text_widget.insert(tk.END, header)
            text_widget.insert(tk.END, separator)

            text_widget.tag_configure("correct", foreground=COLOR_CORRECT)
            text_widget.tag_configure("wrong", foreground=COLOR_WRONG)
            text_widget.tag_configure("warning", foreground=COLOR_WARNING)
            text_widget.tag_configure("neutral", foreground=COLOR_TEXT)

            for entry in self.game_history:
                q = entry.get('question', 'N/A')
                ua = str(entry.get('user_answer', 'N/A'))
                ca = str(entry.get('correct_answer', 'N/A'))
                r = entry.get('result', 'Unknown')
                tag = "neutral"
                r_display = r # Default display

                if r == "Correct": r_display, tag = "✅ Correct", "correct"
                elif r == "Correct (Retry)": r_display, tag = "✅ Correct (Retry)", "correct"
                elif r == "Wrong (Retry Failed)": r_display, tag = "❌ Wrong (Retry)", "wrong"
                elif r == "Wrong (Skipped)": r_display, tag = "❌ Wrong (Skipped)", "wrong"
                elif r == "Timeout": r_display, tag = "⏱ Timeout", "warning"
                elif "Invalid" in r: r_display, tag = f"⚠️ {r}", "warning"
                elif r == "Error": r_display, tag = f"⚙️ Error", "warning"

                line = f"{q:<{q_width}} {ua:<{ua_width}} {ca:<{ca_width}} {r_display:<{r_width}}\n"
                text_widget.insert(tk.END, line, (tag,))

        text_widget.config(state=tk.DISABLED)

    def end_game(self):
        if self.timer_id: self.root.after_cancel(self.timer_id); self.timer_id = None
        save_score(self.player_name, self.score, self.difficulty_mode)
        self.mode_played_label.config(text=f"Mode Played: {self.difficulty_mode.capitalize()}")
        self.final_score_label.config(text=f"Your final score: {self.score}/{TOTAL_QUESTIONS}")

        self.display_game_summary(self.summary_text) # Display summary
        self.display_leaderboard(self.leaderboard_text)

        self.show_frame(self.end_frame)

    def display_leaderboard(self, text_widget):
        """Formats and displays the leaderboard in the provided Text widget."""
        scores = load_scores()
        text_widget.config(state=tk.NORMAL)
        text_widget.delete('1.0', tk.END)
        if not scores:
            text_widget.insert(tk.END, "No scores yet! Be the first! ✨")
        else:
            medals = ['🥇', '🥈', '🥉', '🎖️', '🎖️']
            name_width, score_width = 25, 20
            text_widget.insert(tk.END, f"{'Rank':<6} {'Name':<{name_width}} {'Score':<{score_width}}\n")
            text_widget.insert(tk.END, "="*(6 + name_width + score_width + 2) + "\n")
            for i, (name, score_val, score_str) in enumerate(scores[:5]):
                 medal_index = min(i, len(medals) - 1)
                 line = f"{medals[medal_index]:<6} {name:<{name_width}} {score_str:<{score_width}}\n"
                 text_widget.insert(tk.END, line)
        text_widget.config(state=tk.DISABLED)

    def show_leaderboard_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("🏆 Leaderboard")
        popup.geometry("450x300")
        popup.configure(bg=COLOR_BACKGROUND)
        tk.Label(popup, text="🏆 Leaderboard (Top 5) 🏆", font=self.label_font, bg=COLOR_BACKGROUND, fg=COLOR_TITLE).pack(pady=15)
        lb_text = scrolledtext.ScrolledText(popup, height=8, width=55, font=self.leaderboard_font, relief="solid", borderwidth=1, bg=COLOR_LEADERBOARD_BG, fg=COLOR_TEXT, wrap=tk.NONE)
        lb_text.pack(pady=5, padx=15)
        self.display_leaderboard(lb_text)
        tk.Button(popup, text="Close", font=self.button_font, command=popup.destroy, width=10, pady=3, bg=COLOR_QUIT, fg=COLOR_QUIT_TEXT, activebackground=COLOR_QUIT_HOVER, activeforeground=COLOR_QUIT_TEXT, relief="raised", borderwidth=2).pack(pady=15)
        popup.transient(self.root); popup.grab_set(); self.root.wait_window(popup)

    def play_again(self):
        self.show_frame(self.start_frame)

# ========== Main Execution ==========

if __name__ == "__main__":
    root = tk.Tk()
    app = MindMathGUI(root)
    root.mainloop()
