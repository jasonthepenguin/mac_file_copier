import tkinter as tk
from tkinter import ttk, filedialog
import os
from pathlib import Path
from AppKit import NSPasteboard, NSArray  # Requires pyobjc-framework-AppKit
from Foundation import NSURL

class CodeFileCopier:
    def __init__(self, root):
        self.root = root
        self.root.title("Fake Ass Cursor")
        self.root.attributes('-topmost', True)
        self.current_dir = None
        self.file_paths = {}
        
        # Configure root window
        self.root.configure(bg='#1e1e1e')
        self.root.minsize(400, 500)
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TLabel', 
                       background='#1e1e1e', 
                       foreground='#d4d4d4', 
                       font=('Helvetica', 11))
        
        style.configure('TButton',
                       background='#2d2d2d',
                       foreground='#ffffff',
                       borderwidth=0,
                       font=('Helvetica', 11, 'bold'),
                       padding=8)
        style.map('TButton',
                 background=[('active', '#404040'), ('pressed', '#505050')],
                 foreground=[('active', '#ffffff')])
        
        # Main container
        self.main_frame = ttk.Frame(root, padding="15")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights for responsiveness
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Directory selection
        self.dir_frame = ttk.Frame(self.main_frame)
        self.dir_frame.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        self.dir_frame.grid_columnconfigure(0, weight=1)
        
        self.dir_label = ttk.Label(self.dir_frame, text="No directory selected", wraplength=300)
        self.dir_label.grid(row=0, column=0, padx=5, sticky="w")
        
        self.select_btn = ttk.Button(self.dir_frame, text="Select Directory", command=self.select_directory)
        self.select_btn.grid(row=0, column=1, padx=5, sticky="e")
        
        # Extensions entry
        self.ext_frame = ttk.Frame(self.main_frame)
        self.ext_frame.grid(row=1, column=0, pady=(0, 15), sticky="ew")
        self.ext_frame.grid_columnconfigure(1, weight=1)
        
        self.ext_label = ttk.Label(self.ext_frame, text="File extensions:")
        self.ext_label.grid(row=0, column=0, padx=5, sticky="w")
        
        self.ext_entry = tk.Entry(self.ext_frame, bg='#2d2d2d', fg='#d4d4d4', 
                                insertbackground='white', relief='flat')
        self.ext_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.ext_entry.insert(0, ".py, .cpp, .c, .java, .js")
        
        # Ignored folders
        self.ignore_frame = ttk.Frame(self.main_frame)
        self.ignore_frame.grid(row=2, column=0, pady=(0, 15), sticky="ew")
        self.ignore_frame.grid_columnconfigure(1, weight=1)
        
        self.ignore_label = ttk.Label(self.ignore_frame, text="Ignore folders:")
        self.ignore_label.grid(row=0, column=0, padx=5, sticky="w")
        
        self.ignore_entry = tk.Entry(self.ignore_frame, bg='#2d2d2d', fg='#d4d4d4',
                                   insertbackground='white', relief='flat')
        self.ignore_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.ignore_entry.insert(0, "node_modules, __pycache__, .git")
        
        # File list
        self.list_frame = ttk.Frame(self.main_frame)
        self.list_frame.grid(row=3, column=0, pady=(0, 15), sticky="nsew")
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.list_frame.grid_columnconfigure(0, weight=1)
        
        self.scrollbar = tk.Scrollbar(self.list_frame, bg='#2d2d2d', 
                                    troughcolor='#1e1e1e', bd=0)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.file_list = tk.Listbox(self.list_frame,
                                  selectmode='multiple',
                                  bg='#252525',
                                  fg='#d4d4d4',
                                  selectbackground='#404040',
                                  selectforeground='#ffffff',
                                  highlightthickness=0,
                                  borderwidth=0,
                                  height=25,
                                  font=('Helvetica', 12),
                                  exportselection=0)
        self.file_list.grid(row=0, column=0, sticky="nsew")
        self.file_list.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.file_list.yview)
        
        # Buttons frame
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.grid(row=4, column=0, pady=(0, 10), sticky="ew")
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)
        
        self.copy_btn = ttk.Button(self.btn_frame, text="Copy Files", command=self.copy_files)
        self.copy_btn.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.refresh_btn = ttk.Button(self.btn_frame, text="Refresh", command=self.refresh_list)
        self.refresh_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Search frame (moved from row 2 to row 6)
        self.search_frame = ttk.Frame(self.main_frame)
        self.search_frame.grid(row=6, column=0, pady=(0, 10), sticky="ew")
        self.search_frame.grid_columnconfigure(1, weight=1)
        
        self.search_label = ttk.Label(self.search_frame, text="Search:")
        self.search_label.grid(row=0, column=0, padx=5, sticky="w")
        
        self.search_entry = tk.Entry(self.search_frame, bg='#2d2d2d', fg='#d4d4d4',
                                   insertbackground='white', relief='flat')
        self.search_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.search_entry.config(bd=1, highlightthickness=1, highlightbackground='#404040')
        self.search_entry.bind('<KeyRelease>', self.filter_files)
        
        # Status label (moved to row 7)
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=7, column=0, pady=5, sticky="ew")
        
        # Add subtle border to entries
        for entry in (self.ext_entry, self.ignore_entry):
            entry.config(bd=1, highlightthickness=1, highlightbackground='#404040')

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.current_dir = directory
            self.dir_label.config(text=f"Selected: {directory}")
            self.refresh_list()
            self.status_label.config(text="")
            
    def get_code_files(self, directory):
        extensions_input = self.ext_entry.get()
        code_extensions = {ext.strip().lower() for ext in extensions_input.split(',') if ext.strip()}
        
        ignore_input = self.ignore_entry.get()
        ignore_folders = {folder.strip().lower() for folder in ignore_input.split(',') if folder.strip()}
        
        code_files_by_ext = {}
        try:
            for root, dirs, files in os.walk(directory):
                dirs[:] = [d for d in dirs if d.lower() not in ignore_folders]
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in code_extensions:
                        full_path = os.path.join(root, file)
                        if ext not in code_files_by_ext:
                            code_files_by_ext[ext] = []
                        code_files_by_ext[ext].append(full_path)
        except Exception as e:
            self.status_label.config(text=f"Error scanning directory: {e}")
        return code_files_by_ext
    
    def refresh_list(self):
        if not self.current_dir:
            return
            
        self.file_list.delete(0, tk.END)
        code_files_by_ext = self.get_code_files(self.current_dir)
        
        if not code_files_by_ext:
            self.file_list.insert(tk.END, "No matching files found")
            return
            
        # Store the full file data for filtering
        self.all_files_data = []
        self.file_paths = {}
        current_index = 0
            
        for ext in sorted(code_files_by_ext.keys()):
            header = f"=== {ext.upper()[1:]} Files ==="
            self.all_files_data.append(("header", header, None))
            self.file_list.insert(tk.END, header)
            current_index += 1
            
            sorted_files = sorted(code_files_by_ext[ext])
            for file_path in sorted_files:
                filename = os.path.basename(file_path)
                self.all_files_data.append(("file", filename, file_path))
                self.file_list.insert(tk.END, f"  {filename}")
                self.file_paths[current_index] = file_path
                current_index += 1
                
            self.all_files_data.append(("spacer", "", None))
            self.file_list.insert(tk.END, "")
            current_index += 1

    def filter_files(self, event=None):
        search_term = self.search_entry.get().lower()
        
        # Remember selected filenames before clearing
        selected_indices = self.file_list.curselection()
        selected_files = {self.file_list.get(i).strip() for i in selected_indices}
        
        self.file_list.delete(0, tk.END)
        
        if not hasattr(self, 'all_files_data'):
            return
            
        self.file_paths = {}
        current_index = 0
        current_ext = None
        has_matches = False
        
        for item_type, text, file_path in self.all_files_data:
            if item_type == "file":
                if search_term in text.lower():
                    if not has_matches:
                        has_matches = True
                    self.file_list.insert(tk.END, f"  {text}")
                    self.file_paths[current_index] = file_path
                    # Restore selection if this file was previously selected
                    if text in selected_files:
                        self.file_list.selection_set(current_index)
                    current_index += 1
        
        if not has_matches:
            self.file_list.insert(tk.END, "No matching files found")

    def copy_files(self):
        if not self.current_dir:
            self.status_label.config(text="No directory selected")
            return
            
        selected_indices = self.file_list.curselection()
        if not selected_indices:
            self.status_label.config(text="No files selected")
            return
            
        try:
            selected_files = []
            for index in selected_indices:
                item = self.file_list.get(index)
                if not item.startswith("===") and item.strip():
                    # Use the stored full path instead of building it from the displayed name
                    if index in self.file_paths:
                        selected_files.append(self.file_paths[index])
            
            pb = NSPasteboard.generalPasteboard()
            pb.clearContents()
            file_urls = [NSURL.fileURLWithPath_(path) for path in selected_files]
            success = pb.writeObjects_(NSArray.arrayWithArray_(file_urls))
            
            if success:
                self.status_label.config(text=f"Copied {len(selected_files)} file(s) to clipboard")
                self.copy_btn.config(text="Copied!")
                self.root.after(1000, lambda: self.copy_btn.config(text="Copy Files"))
            else:
                self.status_label.config(text="Failed to copy files to clipboard")
                
        except Exception as e:
            self.status_label.config(text=f"Error copying files: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeFileCopier(root)
    root.mainloop()