import tkinter as tk
from tkinter import ttk, messagebox
from app.models.mindmap import MindMap, Node

class EditDialog:
    """Dialog for editing mind map nodes"""
    
    def __init__(self, parent, mindmap: MindMap, node: Node):
        self.mindmap = mindmap
        self.node = node
        self.result = None
        self.action = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Edit Node: {node.label}")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
        
        # Node info
        info_frame = ttk.Frame(self.dialog, padding="10")
        info_frame.pack(fill=tk.X)
        
        ttk.Label(info_frame, text=f"Node Type: {node.node_type}", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Edit label
        label_frame = ttk.Frame(self.dialog, padding="10")
        label_frame.pack(fill=tk.X)
        
        ttk.Label(label_frame, text="Node Label:").pack(anchor=tk.W)
        self.label_entry = ttk.Entry(label_frame, width=50)
        self.label_entry.insert(0, node.label)
        self.label_entry.pack(fill=tk.X, pady=(5, 0))
        self.label_entry.select_range(0, tk.END)
        self.label_entry.focus()
        
        # Add child node section
        if node.node_type != 'child':  # Can add children to root and branches
            child_frame = ttk.LabelFrame(self.dialog, text="Add Child Node", padding="10")
            child_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(child_frame, text="New Child Label:").pack(anchor=tk.W)
            self.child_entry = ttk.Entry(child_frame, width=50)
            self.child_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Expand with AI button
        if node.node_type != 'child':  # Can expand root and branches
            ai_frame = ttk.Frame(self.dialog, padding="10")
            ai_frame.pack(fill=tk.X)
            
            ttk.Button(
                ai_frame,
                text="Expand with AI",
                command=self.on_expand_ai
            ).pack(side=tk.LEFT)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding="10")
        button_frame.pack(fill=tk.X)
        
        if node.node_type != 'root':  # Can delete non-root nodes
            ttk.Button(
                button_frame,
                text="Delete Node",
                command=self.on_delete
            ).pack(side=tk.LEFT)
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self.on_save
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel
        ).pack(side=tk.RIGHT)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.on_save())
        self.dialog.bind('<Escape>', lambda e: self.on_cancel())
    
    def on_save(self):
        """Handle save button click"""
        new_label = self.label_entry.get().strip()
        if not new_label:
            messagebox.showwarning("Warning", "Label cannot be empty.")
            return
        
        if new_label != self.node.label:
            self.result = {'action': 'update', 'label': new_label}
        else:
            self.result = {'action': 'none'}
        
        # Check if adding child
        if hasattr(self, 'child_entry'):
            child_label = self.child_entry.get().strip()
            if child_label:
                if self.result['action'] == 'none':
                    self.result = {'action': 'add_child', 'label': child_label}
                else:
                    self.result['add_child'] = child_label
        
        self.dialog.destroy()
    
    def on_expand_ai(self):
        """Handle expand with AI button click"""
        self.result = {'action': 'expand_ai'}
        self.dialog.destroy()
    
    def on_delete(self):
        """Handle delete button click"""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{self.node.label}' and all its children?"):
            self.result = {'action': 'delete'}
            self.dialog.destroy()
    
    def on_cancel(self):
        """Handle cancel button click"""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and return result"""
        self.dialog.wait_window()
        return self.result

