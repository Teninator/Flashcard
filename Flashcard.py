import openai
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import PyPDF2
import threading
import os  # For environment variables

class FlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flashcard App")
        self.root.geometry("600x600")
        self.flashcards = []
        self.current_card = 0
        self.night_mode = False
        self.cancelled = False  # To track if the operation is cancelled

        # Setup the UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface."""
        # Main frame for content
        self.main_frame = tk.Frame(self.root, padx=20, pady=20, bg="white")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Top frame for toggle button
        top_frame = tk.Frame(self.main_frame, padx=20, pady=10, bg="white")
        top_frame.pack(fill=tk.X, side=tk.TOP)

        # Night mode toggle button (Top right)
        self.toggle_button = tk.Button(top_frame, text="Toggle Night Mode", command=self.toggle_night_mode, font=("Arial", 12), bg="#6c757d", fg="white")
        self.toggle_button.pack(side=tk.RIGHT)

        # Upload button
        self.upload_button = tk.Button(self.main_frame, text="Upload PDF for Flashcards", command=self.upload_pdf, font=("Arial", 12), bg="#007BFF", fg="white")
        self.upload_button.pack(pady=10)

        # Summarize button
        self.summarize_button = tk.Button(self.main_frame, text="Summarize Document", command=self.summarize_document, font=("Arial", 12), bg="#28A745", fg="white")
        self.summarize_button.pack(pady=10)

        # Label for analysis feedback
        self.analysis_label = tk.Label(self.main_frame, text="", font=("Arial", 12), bg="white")
        self.analysis_label.pack(pady=10)

        # Label for uploaded document name
        self.uploaded_doc_label = tk.Label(self.main_frame, text="", font=("Arial", 12), bg="white")
        self.uploaded_doc_label.pack(pady=10)

        # Text widget for displaying document summary (non-editable)
        self.summary_text = tk.Text(self.main_frame, wrap=tk.WORD, height=10, width=50, font=("Arial", 12), padx=10, pady=10, bg="light grey")
        self.summary_text.pack(pady=10)
        self.summary_text.config(state=tk.DISABLED)

        # Flashcard count input
        self.num_flashcards_label = tk.Label(self.main_frame, text="Number of flashcards to generate:", font=("Arial", 12), bg="white")
        self.num_flashcards_label.pack(pady=5)

        self.num_flashcards_entry = tk.Entry(self.main_frame, width=10, font=("Arial", 12))
        self.num_flashcards_entry.insert(0, "10")  # Default value
        self.num_flashcards_entry.pack(pady=5)

        # Progress bar
        self.progress_bar = ttk.Progressbar(self.main_frame, length=300, mode='determinate')
        self.progress_bar.pack(pady=20)

        # Loading label
        self.loading_label = tk.Label(self.main_frame, text="", font=("Arial", 12), bg="white")
        self.loading_label.pack(pady=10)

        # Cancel button
        self.cancel_button = tk.Button(self.main_frame, text="Cancel", command=self.cancel_operation, font=("Arial", 12), bg="#DC3545", fg="white")
        self.cancel_button.pack(pady=10)

    def toggle_night_mode(self):
        """Toggle night mode on or off."""
        self.night_mode = not self.night_mode
        bg_color = "black" if self.night_mode else "white"
        fg_color = "white" if self.night_mode else "black"

        self.root.config(bg=bg_color)
        self.main_frame.config(bg=bg_color)
        self.analysis_label.config(bg=bg_color, fg=fg_color)
        self.uploaded_doc_label.config(bg=bg_color, fg=fg_color)
        self.loading_label.config(bg=bg_color, fg=fg_color)

        for widget in self.main_frame.winfo_children():
            if isinstance(widget, tk.Button) or isinstance(widget, tk.Entry) or isinstance(widget, tk.Label):
                widget.config(bg=bg_color, fg=fg_color)

        self.summary_text.config(bg="light grey" if self.night_mode else "white", fg=fg_color)

    def upload_pdf(self):
        """Upload and analyze a PDF."""
        pdf_file_path = filedialog.askopenfilename(title="Select a PDF", filetypes=[("PDF files", "*.pdf")])
        if pdf_file_path:
            self.cancelled = False  # Reset the cancelled flag
            self.analysis_label.config(text="Analyzing document...")
            self.loading_label.config(text="")
            self.uploaded_doc_label.config(text=f"Uploaded Document: {pdf_file_path.split('/')[-1]}")
            self.root.update()  # Update the GUI

            threading.Thread(target=self.extract_flashcards, args=(pdf_file_path,), daemon=True).start()

    def extract_flashcards(self, filepath):
        """Extract text from PDF and create flashcards."""
        self.progress_bar['value'] = 0
        self.flashcards = []
        total_pages = 0

        try:
            num_flashcards = int(self.num_flashcards_entry.get())
            if num_flashcards <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid positive number for flashcards.")
            return

        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)

            for i, page in enumerate(reader.pages):
                if self.cancelled:
                    self.analysis_label.config(text="Operation cancelled.")
                    self.loading_label.config(text="")
                    return

                text = page.extract_text()
                if text:
                    lines = text.splitlines()
                    for line in lines:
                        if len(self.flashcards) >= num_flashcards:
                            break
                        if line.strip():
                            question, answer = self.create_flashcard_pair(line.strip())
                            self.flashcards.append((question, answer))

                self.progress_bar['value'] = (i + 1) / total_pages * 100
                self.root.update_idletasks()

        if self.flashcards:
            self.analysis_label.config(text="Flashcards generated!")
            self.show_flashcard_screen()  # Open flashcard window
        else:
            self.analysis_label.config(text="No text found. Please check the document format.")
        self.progress_bar['value'] = 0

    def create_flashcard_pair(self, line):
        """Create a question and answer from text."""
        question = f"What is: '{line}'?"
        answer = f"This is the answer: {line}"  # Placeholder answer
        return question, answer

    def cancel_operation(self):
        """Cancel the current operation."""
        self.cancelled = True
        self.loading_label.config(text="Operation cancelled.")

    def summarize_document(self):
        """Summarize the document using OpenAI's API."""
        if not self.flashcards:
            messagebox.showwarning("No Document", "Please upload a document first.")
            return

        self.loading_label.config(text="Summarizing document...")
        self.root.update()

        # Replace with your OpenAI API key from environment variables
        openai.api_key = os.getenv("OPENAI_API_KEY")

        # Prepare text for summarization
        text_to_summarize = " ".join([f"{q} {a}" for q, a in self.flashcards])
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"Summarize the following content: {text_to_summarize}",
                max_tokens=150,
                temperature=0.7,
            )
            summary_text = response.choices[0].text.strip()

            self.summary_text.config(state=tk.NORMAL)
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, summary_text)
            self.summary_text.config(state=tk.DISABLED)
            self.loading_label.config(text="Summary done!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.loading_label.config(text="Failed to summarize.")

    def show_flashcard_screen(self):
        """Create and display the flashcard window."""
        self.flashcard_window = tk.Toplevel(self.root)
        self.flashcard_window.title("Flashcards")
        self.flashcard_window.geometry("400x400")
        self.current_card = 0  # Reset current card index

        # Create UI for flashcards
        self.question_label = tk.Label(self.flashcard_window, text="", font=("Helvetica", 16), wraplength=300)
        self.question_label.pack(pady=10)

        self.answer_label = tk.Label(self.flashcard_window, text="", font=("Helvetica", 14), wraplength=300)
        self.answer_label.pack(pady=10)

        # Show answer button
        self.show_answer_button = tk.Button(self.flashcard_window, text="Show Question", command=self.show_answer, font=("Arial", 12), bg="#FFC107", fg="black")
        self.show_answer_button.pack(pady=10)

        # Navigation buttons
        button_frame = tk.Frame(self.flashcard_window)
        button_frame.pack(pady=10)

        self.prev_button = tk.Button(button_frame, text="<< Previous", command=self.previous_flashcard, font=("Arial", 12), bg="#007BFF", fg="white")
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.next_button = tk.Button(button_frame, text="Next >>", command=self.next_flashcard, font=("Arial", 12), bg="#007BFF", fg="white")
        self.next_button.pack(side=tk.LEFT, padx=5)

        # Display first card
        self.display_flashcard()

    def display_flashcard(self):
        """Display the current flashcard."""
        if self.flashcards:
            question, answer = self.flashcards[self.current_card]
            self.question_label.config(text=f"Flashcard {self.current_card + 1}/{len(self.flashcards)}: {answer}")  # Start with Answer
            self.answer_label.config(text="")
        else:
            self.question_label.config(text="No flashcards available.")
            self.answer_label.config(text="")

    def show_answer(self):
        """Toggle between showing the question and answer."""
        question, answer = self.flashcards[self.current_card]
        if self.answer_label.cget("text") == "":
            self.answer_label.config(text=question)
            self.show_answer_button.config(text="Show Answer")
        else:
            self.answer_label.config(text="")
            self.show_answer_button.config(text="Show Question")

    def next_flashcard(self):
        """Navigate to the next flashcard."""
        if self.flashcards:
            self.current_card = (self.current_card + 1) % len(self.flashcards)
            self.display_flashcard()

    def previous_flashcard(self):
        """Navigate to the previous flashcard."""
        if self.flashcards:
            self.current_card = (self.current_card - 1) % len(self.flashcards)
            self.display_flashcard()


# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()


