# front/history_tab_ui.py

import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from backend.HistoryManager import HistoryManager
from front.config import APPLE_COLORS, FONTS, MAX_HISTORY_DISPLAY
from front.image_cache import ImageCache

class HistoryTabUI:
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.manager = HistoryManager()
        self.image_cache = ImageCache(max_size_mb=100)
        
        # Filter state
        self.filter_var = tk.StringVar(value="All")
        self.filtered_data = []
        self.all_data = []
        
        # Configure grid
        self.parent.grid_rowconfigure(1, weight=1)
        self.parent.grid_rowconfigure(2, weight=4)  # Increased weight for preview
        self.parent.grid_columnconfigure(0, weight=1)
        
        self._build_ui()
        self._load_history()

    def _build_ui(self):
        # Control frame with reduced padding
        ctrl_frame = ttk.Frame(self.parent, style="AppleCard.TFrame")
        ctrl_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=(20, 5))
        
        ctrl_container = ttk.Frame(ctrl_frame)
        ctrl_container.pack(fill='x', padx=20, pady=12)
        
        # Filter section
        filter_label = ttk.Label(
            ctrl_container,
            text="Filter by diagnosis:",
            style="AppleBody.TLabel"
        )
        filter_label.pack(side='left', padx=(0, 12))
        
        # Filter dropdown
        self.filter_combo = ttk.Combobox(
            ctrl_container,
            textvariable=self.filter_var,
            values=["All", "Normal", "COVID-19", "Pneumonia-Bacterial", "Pneumonia-Viral"],
            state='readonly',
            width=25,
            style="Apple.TCombobox"
        )
        self.filter_combo.pack(side='left', padx=(0, 20))
        self.filter_combo.bind('<<ComboboxSelected>>', self._on_filter_change)
        
        # Clear button
        clear_btn = ttk.Button(
            ctrl_container,
            text="Clear History",
            command=self._clear_history,
            style="AppleSecondary.TButton"
        )
        clear_btn.pack(side='right')
        
        # Results count label
        self.count_label = ttk.Label(
            ctrl_container,
            text="",
            style="AppleSecondary.TLabel"
        )
        self.count_label.pack(side='right', padx=(0, 20))
        
        # Table frame with specific height for 2.5 rows
        self.table_frame = ttk.Frame(self.parent, style="AppleCard.TFrame")
        self.table_frame.grid(row=1, column=0, sticky='ew', padx=20, pady=(5, 10))
        
        # Fixed height container for table
        table_outer = ttk.Frame(self.table_frame, height=195)  # Height for 2.5 rows
        table_outer.pack(fill='x', expand=False, padx=20, pady=15)
        table_outer.pack_propagate(False)
        
        table_container = ttk.Frame(table_outer)
        table_container.pack(fill='both', expand=True)
        
        # Treeview
        cols = ('ImageName', 'Model', 'Result', 'Confidence (%)')
        self.tree = ttk.Treeview(
            table_container,
            columns=cols,
            show='headings',
            selectmode='browse',
            style="Apple.Treeview"
        )
        
        # Remove height specification to let container control it
        
        # Configure columns
        column_widths = {
            'ImageName': 250,
            'Model': 200,
            'Result': 200,
            'Confidence (%)': 250
        }
        
        for col in cols:
            self.tree.heading(col, text=col, anchor='center')
            self.tree.column(col, anchor='center', width=column_widths.get(col, 100))
        
        # Scrollbars
        vsb = ttk.Scrollbar(
            table_container,
            orient='vertical',
            command=self.tree.yview,
            style="Apple.Vertical.TScrollbar"
        )
        self.tree.configure(yscrollcommand=vsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        
        # Preview frame - scrollable
        self.preview_frame = ttk.Frame(self.parent, style="AppleCard.TFrame")
        self.preview_frame.grid(row=2, column=0, sticky='nsew', padx=20, pady=(10, 20))
        
        # Create scrollable preview
        self.preview_canvas = tk.Canvas(self.preview_frame, bg=APPLE_COLORS['surface'], highlightthickness=0)
        self.preview_scrollbar = ttk.Scrollbar(
            self.preview_frame, 
            orient='vertical', 
            command=self.preview_canvas.yview,
            style="Apple.Vertical.TScrollbar"
        )
        self.preview_canvas.configure(yscrollcommand=self.preview_scrollbar.set)
        
        self.preview_canvas.pack(side='left', fill='both', expand=True)
        self.preview_scrollbar.pack(side='right', fill='y')
        
        # Inner frame for content
        self.preview_inner = ttk.Frame(self.preview_canvas)
        self.preview_canvas_window = self.preview_canvas.create_window(0, 0, anchor='nw', window=self.preview_inner)
        
        # Bind canvas resize
        self.preview_canvas.bind('<Configure>', self._on_canvas_configure)
        self.preview_inner.bind('<Configure>', self._on_frame_configure)
        
        # Empty state
        self.empty_state_label = ttk.Label(
            self.preview_inner,
            text="Select an entry to view details",
            style="AppleSecondary.TLabel"
        )
        self.empty_state_label.pack(pady=100)

    def _on_canvas_configure(self, event):
        """Update canvas scroll region"""
        canvas_width = event.width
        self.preview_canvas.itemconfig(self.preview_canvas_window, width=canvas_width)

    def _on_frame_configure(self, event):
        """Update scroll region when frame changes"""
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox('all'))

    def _load_history(self):
        """Load history data"""
        self.all_data = self.manager.get_history()
        # Sort by timestamp (newest first) and limit
        self.all_data.sort(key=lambda x: x.get('Timestamp', ''), reverse=True)
        self._apply_filter()

    def _apply_filter(self):
        """Apply filter to records"""
        filter_value = self.filter_var.get()
        
        if filter_value == "All":
            self.filtered_data = self.all_data[:MAX_HISTORY_DISPLAY]
        else:
            filtered = [r for r in self.all_data if r.get('Result', '') == filter_value]
            self.filtered_data = filtered[:MAX_HISTORY_DISPLAY]
        
        self._update_display()

    def _update_display(self):
        """Update treeview display"""
        # Clear existing
        self.tree.delete(*self.tree.get_children())
        
        if not self.filtered_data:
            # Show empty state
            self.count_label.config(text="No records found")
            return
        
        # Insert filtered items
        for rec in self.filtered_data:
            # Format confidence for display
            probs = str(rec.get('Probabilities', ''))
            prob_lines = []
            
            # Extract all probabilities
            matches = re.findall(r'([\w\-]+): (\d+\.\d+)%', probs)
            for name, value in matches:
                prob_lines.append(f"{name}: {value}%")
            
            confidence_text = '\n'.join(prob_lines) if prob_lines else 'N/A'
            
            self.tree.insert(
                '', 'end',
                iid=rec['ImageName'],
                values=(
                    rec['ImageName'],
                    rec['Model'],
                    rec['Result'],
                    confidence_text
                )
            )
        
        # Update count
        total = len(self.all_data)
        showing = len(self.filtered_data)
        
        if self.filter_var.get() == "All":
            if total > MAX_HISTORY_DISPLAY:
                self.count_label.config(text=f"Showing {showing} of {total} records")
            else:
                self.count_label.config(text=f"{total} records")
        else:
            self.count_label.config(text=f"{showing} filtered records")

    def _on_filter_change(self, event=None):
        """Handle filter change"""
        self._apply_filter()
        
        if not self.filtered_data:
            self.app.show_notification("No matching records found", "info")

    def update_history(self):
        """Refresh history display"""
        self._load_history()

    def _clear_history(self):
        """Clear all history"""
        count = len(self.all_data)
        if count == 0:
            self.app.show_notification("History is already empty", "info")
            return
        
        result = messagebox.askyesno(
            "Clear History",
            f"Are you sure you want to clear all {count} history records?\n\n"
            "This action cannot be undone.",
            parent=self.app.root
        )
        
        if result:
            self.manager.clear_history()
            self.image_cache.clear()
            self.update_history()
            
            # Clear preview
            for widget in self.preview_inner.winfo_children():
                widget.destroy()
            
            # Show empty state
            self.empty_state_label = ttk.Label(
                self.preview_inner,
                text="Select an entry to view details",
                style="AppleSecondary.TLabel"
            )
            self.empty_state_label.pack(pady=100)
            
            self.app.show_notification("History cleared successfully", "success")

    def _on_select(self, event):
        """Handle selection change"""
        sel = self.tree.selection()
        if not sel:
            return
        
        name = sel[0]
        record = next((r for r in self.filtered_data if r['ImageName'] == name), None)
        if not record:
            return
        
        # Clear preview area
        for widget in self.preview_inner.winfo_children():
            widget.destroy()
        
        # Container with padding
        container = ttk.Frame(self.preview_inner)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Create two columns
        content_frame = ttk.Frame(container)
        content_frame.pack(fill='both', expand=True)
        
        # Left column for image
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side='left', fill='both', expand=True)
        
        # Right column for metrics
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side='left', fill='both', expand=True, padx=(20, 0))
        
        # Display image
        path = record.get('Path', '')
        if path and os.path.isfile(path):
            self._display_image(left_frame, path)
        else:
            # Image not found
            error_label = ttk.Label(
                left_frame,
                text="Image file not found",
                style="AppleSecondary.TLabel"
            )
            error_label.pack(pady=20)
            self.app.show_notification("Image file not found", "warning")
        
        # Display metrics vertically
        self._display_metrics_vertical(right_frame, record)

    def _display_image(self, parent, path):
        """Display image with proper scaling"""
        try:
            # Load original image
            img = Image.open(path)
            
            # Calculate scale to fit while maintaining aspect ratio
            max_width = 400
            max_height = 400
            
            # Calculate scaling factor
            scale = min(max_width / img.width, max_height / img.height)
            
            # Only scale down, not up
            if scale < 1:
                new_width = int(img.width * scale)
                new_height = int(img.height * scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            
            # Container for centering
            img_container = ttk.Frame(parent)
            img_container.pack(expand=True)
            
            img_label = ttk.Label(img_container, image=photo, anchor='center')
            img_label.image = photo  # Keep reference
            img_label.pack()
            
        except Exception as e:
            self.app.show_notification(f"Failed to load image: {str(e)}", "error")

    def _display_metrics_vertical(self, parent, record):
        """Display metrics vertically with proper order"""
        # Title
        title = ttk.Label(
            parent,
            text="Analysis Results",
            style="AppleTitle.TLabel"
        )
        title.pack(anchor='w', pady=(0, 20))
        
        # Primary result
        result_label = ttk.Label(
            parent,
            text=f"Primary Diagnosis: {record.get('Result', 'Unknown')}",
            font=(FONTS['system'][0], 16, 'bold'),
            foreground=APPLE_COLORS['primary']
        )
        result_label.pack(anchor='w', pady=(0, 20))
        
        # Parse probabilities
        probs = str(record.get('Probabilities', ''))
        prob_dict = {}
        matches = re.findall(r'([\w\-]+): (\d+\.\d+)%', probs)
        for name, value in matches:
            prob_dict[name] = value
        
        # Display in specific order
        order = ["COVID-19", "Normal", "Pneumonia-Bacterial", "Pneumonia-Viral"]
        
        prob_label = ttk.Label(
            parent,
            text="Probability Distribution:",
            style="AppleSecondary.TLabel"
        )
        prob_label.pack(anchor='w', pady=(0, 10))
        
        for name in order:
            if name in prob_dict:
                value = prob_dict[name]
                
                # Container for each probability
                prob_frame = ttk.Frame(parent)
                prob_frame.pack(fill='x', pady=5)
                
                # Name on left
                name_label = ttk.Label(
                    prob_frame,
                    text=f"{name}:",
                    font=(FONTS['system'][0], FONTS['body_medium'])
                )
                name_label.pack(side='left')
                
                # Value on right
                color = APPLE_COLORS['success'] if float(value) > 75 else APPLE_COLORS['text_primary']
                value_label = ttk.Label(
                    prob_frame,
                    text=f"{value}%",
                    font=(FONTS['system'][0], FONTS['body_medium'], 'bold'),
                    foreground=color
                )
                value_label.pack(side='right')
        
        # Separator
        separator = ttk.Frame(parent, height=1, style="AppleCard.TFrame")
        separator.pack(fill='x', pady=20)
        
        # File info
        file_label = ttk.Label(
            parent,
            text=f"File: {record.get('ImageName', 'Unknown')}",
            style="AppleSecondary.TLabel"
        )
        file_label.pack(anchor='w', pady=(0, 5))
        
        # Model info
        model_label = ttk.Label(
            parent,
            text=f"Model: {record.get('Model', 'Unknown')}",
            style="AppleSecondary.TLabel"
        )
        model_label.pack(anchor='w')