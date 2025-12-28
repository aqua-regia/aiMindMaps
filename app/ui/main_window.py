import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
from app.models.mindmap import MindMap
from app.services.mindmap_service import MindMapService
from app.services.visualization_service import VisualizationService
from app.ui.input_dialog import InputDialog
from app.ui.edit_dialog import EditDialog
from config import Config

class MainWindow:
    """Main application window"""
    
    def __init__(self, mindmap_service: MindMapService, visualization_service: VisualizationService):
        self.mindmap_service = mindmap_service
        self.visualization_service = visualization_service
        self.current_mindmap: MindMap = None
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("AI Mind Map Generator")
        self.root.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        
        # Create menu bar
        self._create_menu()
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Mind map list
        left_panel = ttk.Frame(main_frame, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        ttk.Label(left_panel, text="Saved Mind Maps", font=("Arial", 12, "bold")).pack(pady=(0, 5))
        
        # Create new button in left panel
        ttk.Button(
            left_panel,
            text="➕ Create New Mind Map",
            command=self.create_new_mindmap
        ).pack(fill=tk.X, pady=(0, 10))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.mindmap_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.mindmap_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.mindmap_listbox.bind('<<ListboxSelect>>', self.on_mindmap_select)
        scrollbar.config(command=self.mindmap_listbox.yview)
        
        # Buttons for mind map list
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Refresh", command=self.refresh_mindmap_list).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Delete", command=self.delete_selected_mindmap).pack(fill=tk.X, pady=2)
        
        # Right panel - Mind map display
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Header with title and create button
        header_frame = ttk.Frame(right_panel)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Mind Map Preview", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Prominent "Create New" button
        create_button = ttk.Button(
            header_frame,
            text="➕ Create New Mind Map",
            command=self.create_new_mindmap,
            width=25
        )
        create_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Canvas for displaying mind map image
        canvas_frame = ttk.Frame(right_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Welcome message label (will be shown/hidden as needed)
        self.welcome_label = None
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load mind maps
        self.refresh_mindmap_list()
        
        # Show welcome message if no mind maps
        self._show_welcome_if_empty()
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Mind Map", command=self.create_new_mindmap, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Save Image", command=self.save_current_image, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Edit Current Mind Map", command=self.edit_current_mindmap, accelerator="Ctrl+E")
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.create_new_mindmap())
        self.root.bind('<Control-s>', lambda e: self.save_current_image())
        self.root.bind('<Control-e>', lambda e: self.edit_current_mindmap())
    
    def create_new_mindmap(self):
        """Create a new mind map from text input"""
        dialog = InputDialog(self.root)
        text, title = dialog.show()
        
        if text:
            self.status_var.set("Creating mind map...")
            self.root.update()
            
            try:
                mindmap = self.mindmap_service.create_from_text(text, title)
                self.current_mindmap = mindmap
                self.refresh_mindmap_list()
                self.display_mindmap(mindmap)
                self.status_var.set(f"Mind map '{mindmap.title}' created successfully!")
                # Hide welcome message
                self._show_welcome_if_empty()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create mind map: {str(e)}")
                self.status_var.set("Error creating mind map")
    
    def refresh_mindmap_list(self):
        """Refresh the list of saved mind maps"""
        self.mindmap_listbox.delete(0, tk.END)
        mindmaps = self.mindmap_service.get_all_mindmaps()
        for mindmap in mindmaps:
            self.mindmap_listbox.insert(tk.END, f"{mindmap.title} ({mindmap.id[:8]}...)")
        # Update welcome message visibility
        self._show_welcome_if_empty()
    
    def on_mindmap_select(self, event):
        """Handle mind map selection from list"""
        selection = self.mindmap_listbox.curselection()
        if selection:
            index = selection[0]
            mindmaps = self.mindmap_service.get_all_mindmaps()
            if index < len(mindmaps):
                mindmap = mindmaps[index]
                self.current_mindmap = mindmap
                self.display_mindmap(mindmap)
                self.status_var.set(f"Loaded: {mindmap.title}")
    
    def _show_welcome_if_empty(self):
        """Show welcome message if no mind maps exist"""
        mindmaps = self.mindmap_service.get_all_mindmaps()
        if len(mindmaps) == 0 and not self.current_mindmap:
            self.canvas.delete("all")
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            if canvas_width < 10:
                canvas_width = 600
            if canvas_height < 10:
                canvas_height = 400
            
            # Create welcome text on canvas
            welcome_text = "👋 Welcome!\n\nClick '➕ Create New Mind Map' button above\nor use File → New Mind Map (Ctrl+N)\n\nto create your first mind map"
            self.canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text=welcome_text,
                font=("Arial", 14),
                fill="gray",
                justify=tk.CENTER,
                width=canvas_width - 40,
                tags="welcome"
            )
    
    def display_mindmap(self, mindmap: MindMap):
        """Display a mind map in the canvas"""
        try:
            # Clear welcome message
            self.canvas.delete("welcome")
            
            # Generate visualization (PNG format for tkinter)
            image_path = self.visualization_service.draw_mindmap(mindmap, format='png')
            
            # Load and display image
            img = Image.open(image_path)
            # Resize to fit canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                img.thumbnail((canvas_width - 20, canvas_height - 20), Image.Resampling.LANCZOS)
            
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(
                canvas_width // 2 if canvas_width > 1 else 400,
                canvas_height // 2 if canvas_height > 1 else 300,
                image=self.photo,
                anchor=tk.CENTER
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display mind map: {str(e)}")
    
    def edit_current_mindmap(self):
        """Edit the current mind map"""
        if not self.current_mindmap:
            messagebox.showinfo("Info", "Please select or create a mind map first.")
            return
        
        # Show node selection dialog
        self._show_node_selection_dialog()
    
    def _show_node_selection_dialog(self):
        """Show dialog to select and edit nodes"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Mind Map Nodes")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"500x600+{x}+{y}")
        
        ttk.Label(dialog, text="Select a node to edit:", font=("Arial", 10, "bold")).pack(pady=10)
        
        # Tree view for nodes
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree = ttk.Treeview(tree_frame, yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree.yview)
        
        # Populate tree
        def add_node_to_tree(node, parent=""):
            item = tree.insert(parent, "end", text=node.label, values=(node.id, node.node_type))
            for child in node.children:
                add_node_to_tree(child, item)
        
        add_node_to_tree(self.current_mindmap.root)
        tree.expand_all()
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_edit():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a node to edit.")
                return
            
            item = selection[0]
            node_id = tree.item(item, "values")[0]
            node = self.current_mindmap.find_node(node_id)
            
            if node:
                edit_dialog = EditDialog(dialog, self.current_mindmap, node)
                result = edit_dialog.show()
                
                if result:
                    try:
                        if result['action'] == 'update':
                            self.mindmap_service.update_node(
                                self.current_mindmap.id,
                                node_id,
                                result['label']
                            )
                            self.status_var.set("Node updated")
                        elif result['action'] == 'add_child':
                            self.mindmap_service.add_node(
                                self.current_mindmap.id,
                                node_id,
                                result['label']
                            )
                            self.status_var.set("Child node added")
                        elif result['action'] == 'expand_ai':
                            self.status_var.set("Expanding node with AI...")
                            dialog.update()
                            self.mindmap_service.expand_node_with_ai(
                                self.current_mindmap.id,
                                node_id
                            )
                            self.status_var.set("Node expanded with AI")
                        elif result['action'] == 'delete':
                            self.mindmap_service.delete_node(
                                self.current_mindmap.id,
                                node_id
                            )
                            self.status_var.set("Node deleted")
                        
                        # Refresh
                        self.current_mindmap = self.mindmap_service.get_mindmap(self.current_mindmap.id)
                        self.display_mindmap(self.current_mindmap)
                        dialog.destroy()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to update: {str(e)}")
        
        ttk.Button(button_frame, text="Edit Selected", command=on_edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def delete_selected_mindmap(self):
        """Delete the selected mind map"""
        selection = self.mindmap_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a mind map to delete.")
            return
        
        index = selection[0]
        mindmaps = self.mindmap_service.get_all_mindmaps()
        if index < len(mindmaps):
            mindmap = mindmaps[index]
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{mindmap.title}'?"):
                try:
                    self.mindmap_service.delete_mindmap(mindmap.id)
                    self.refresh_mindmap_list()
                    if self.current_mindmap and self.current_mindmap.id == mindmap.id:
                        self.current_mindmap = None
                        self.canvas.delete("all")
                    self.status_var.set("Mind map deleted")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete mind map: {str(e)}")
    
    def save_current_image(self):
        """Save the current mind map image"""
        if not self.current_mindmap:
            messagebox.showinfo("Info", "No mind map to save.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                image_path = self.visualization_service.draw_mindmap(self.current_mindmap, file_path)
                messagebox.showinfo("Success", f"Image saved to {file_path}")
                self.status_var.set(f"Image saved: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

