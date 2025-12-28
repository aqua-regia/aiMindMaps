import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

class InputDialog:
    """Dialog for text input to create mind maps"""
    
    def __init__(self, parent, title="Create Mind Map"):
        self.result = None
        self.title_text = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
        # Title input
        title_frame = ttk.Frame(self.dialog, padding="10")
        title_frame.pack(fill=tk.X)
        
        ttk.Label(title_frame, text="Mind Map Title (optional):").pack(anchor=tk.W)
        self.title_entry = ttk.Entry(title_frame, width=50)
        self.title_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Text input
        text_frame = ttk.Frame(self.dialog, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(text_frame, text="Enter text to create mind map:").pack(anchor=tk.W)
        self.text_input = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            width=60,
            height=15
        )
        self.text_input.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.text_input.focus()
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="Create",
            command=self.on_create
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel
        ).pack(side=tk.RIGHT)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.on_create())
        self.dialog.bind('<Escape>', lambda e: self.on_cancel())
    
    def on_create(self):
        """Handle create button click"""
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text to create a mind map.")
            return
        
        self.result = text
        self.title_text = self.title_entry.get().strip()
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle cancel button click"""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and return result"""
        self.dialog.wait_window()
        return self.result, self.title_text

