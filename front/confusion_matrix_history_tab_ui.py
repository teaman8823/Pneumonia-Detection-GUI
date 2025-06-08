# front/confusion_matrix_history_tab_ui.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from backend.ConfusionMatrixManager import ConfusionMatrixManager
from front.config import APPLE_COLORS, FONTS, MAX_HISTORY_DISPLAY, IMAGE_PREVIEW_SIZE
from front.image_cache import ImageCache

class ConfusionMatrixHistoryTabUI:
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.manager = ConfusionMatrixManager()
        self.image_cache = ImageCache(max_size_mb=100)
        
        # Data management
        self.all_records = []
        self.displayed_records = []
        self.display_limit = MAX_HISTORY_DISPLAY
        
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
        
        # Count label on left
        self.count_label = ttk.Label(
            ctrl_container,
            text="",
            style="AppleSecondary.TLabel"
        )
        self.count_label.pack(side='left')
        
        # Clear button on right
        clear_btn = ttk.Button(
            ctrl_container,
            text="Clear History",
            command=self._clear_history,
            style="AppleSecondary.TButton"
        )
        clear_btn.pack(side='right')
        
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
        cols = ('Dataset', 'Model', 'Metrics')
        self.tree = ttk.Treeview(
            table_container,
            columns=cols,
            show='headings',
            selectmode='browse',
            style="Apple.Treeview"
        )
        
        # Configure columns
        column_widths = {
            'Dataset': 250,
            'Model': 250,
            'Metrics': 400
        }
        
        for col in cols:
            self.tree.heading(col, text=col, anchor='center')
            self.tree.column(col, anchor='center', width=column_widths.get(col, 100))
        
        # Scrollbar
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
        
        # Load more button
        self.load_more_btn = ttk.Button(
            table_container,
            text="Load More",
            command=self._load_more,
            style="AppleSecondary.TButton"
        )
        
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
        self._show_empty_state()

    def _on_canvas_configure(self, event):
        """Update canvas scroll region"""
        canvas_width = event.width
        self.preview_canvas.itemconfig(self.preview_canvas_window, width=canvas_width)

    def _on_frame_configure(self, event):
        """Update scroll region when frame changes"""
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox('all'))

    def _show_empty_state(self):
        """Show empty state in preview area"""
        for widget in self.preview_inner.winfo_children():
            widget.destroy()
        
        empty_label = ttk.Label(
            self.preview_inner,
            text="Select an evaluation to view confusion matrix",
            style="AppleSecondary.TLabel"
        )
        empty_label.pack(pady=100)

    def _load_history(self):
        """Load evaluation history"""
        self.all_records = self.manager.load_history()
        self.all_records.reverse()  # Newest first
        
        # Reset display
        self.displayed_records = []
        self.display_limit = MAX_HISTORY_DISPLAY
        
        # Clear tree
        self.tree.delete(*self.tree.get_children())
        
        # Display initial records
        self._display_records(0, self.display_limit)
        
        # Update UI
        self._update_ui_state()

    def _display_records(self, start, count):
        """Display records from start index"""
        end = min(start + count, len(self.all_records))
        
        for i in range(start, end):
            rec = self.all_records[i]
            
            # Get dataset name (from new Dataset field)
            dataset_name = rec.get('Dataset', 'Unknown')
            
            # Format metrics for display
            metrics_text = rec.get('Metrics', '')
            lines = []
            for line in metrics_text.split('\n'):
                if ':' in line:
                    metric, value = line.split(':', 1)
                    metric = metric.strip()
                    value = value.strip()
                    
                    if metric.lower() == 'accuracy':
                        lines.append(f"Acc: {value}")
                    elif metric.lower() == 'precision':
                        lines.append(f"Prec: {value}")
                    elif metric.lower() == 'recall':
                        lines.append(f"Rec: {value}")
                    elif metric.lower() == 'f1':
                        lines.append(f"F1: {value}")
            
            formatted_metrics = '\n'.join(lines)
            
            self.tree.insert(
                '', 'end',
                iid=rec['PNGName'],
                values=(
                    dataset_name,
                    rec.get('Model', 'Unknown'),
                    formatted_metrics
                )
            )
        
        self.displayed_records = self.all_records[:end]

    def _update_ui_state(self):
        """Update UI elements based on data state"""
        total = len(self.all_records)
        displayed = len(self.displayed_records)
        
        # Update count label
        if total == 0:
            self.count_label.config(text="No evaluations")
        elif displayed < total:
            self.count_label.config(text=f"Showing {displayed} of {total} evaluations")
        else:
            self.count_label.config(text=f"{total} evaluations")
        
        # Show/hide load more button
        if displayed < total:
            self.load_more_btn.grid(row=2, column=0, pady=(10, 0))
        else:
            self.load_more_btn.grid_forget()

    def _load_more(self):
        """Load more records"""
        current_count = len(self.displayed_records)
        self._display_records(current_count, MAX_HISTORY_DISPLAY)
        self._update_ui_state()

    def _clear_history(self):
        """Clear all history"""
        if not self.all_records:
            self.app.show_notification("History is already empty", "info")
            return
        
        result = messagebox.askyesno(
            "Clear History",
            f"Are you sure you want to clear all {len(self.all_records)} evaluation records?\n\n"
            "This action cannot be undone.",
            parent=self.app.root
        )
        
        if result:
            self.manager.clear_history()
            self.image_cache.clear()
            self._load_history()
            self._show_empty_state()
            self.app.show_notification("Evaluation history cleared", "success")

    def _on_select(self, event):
        """Handle selection change"""
        sel = self.tree.selection()
        if not sel:
            return
        
        key = sel[0]
        record = next((r for r in self.displayed_records if r['PNGName'] == key), None)
        if not record:
            return
        
        # Clear preview area
        for widget in self.preview_inner.winfo_children():
            widget.destroy()
        
        # Container with padding
        container = ttk.Frame(self.preview_inner)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Create two columns layout
        content_frame = ttk.Frame(container)
        content_frame.pack(fill='both', expand=True)
        
        # Left column for matrix
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side='left', fill='both', expand=True)
        
        # Right column for metrics
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side='left', fill='both', expand=True, padx=(20, 0))
        
        # Display matrix
        path = record.get('Path', '')
        if os.path.isfile(path):
            self._display_matrix(left_frame, path)
        else:
            error_label = ttk.Label(
                left_frame,
                text="Confusion matrix image not found",
                style="AppleSecondary.TLabel"
            )
            error_label.pack(pady=20)
            self.app.show_notification("Confusion matrix image not found", "warning")
        
        # Display metrics vertically
        self._display_metrics_vertical(right_frame, record.get('Metrics', ''))

    def _display_matrix(self, parent, path):
        """Display confusion matrix image"""
        try:
            # Load original image
            img = Image.open(path)
            
            # Calculate scale to fit
            max_width = 400
            max_height = 400
            scale = min(max_width / img.width, max_height / img.height)
            
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

    def _display_metrics_vertical(self, parent, metrics_text):
        """Display metrics vertically"""
        # Title
        title = ttk.Label(
            parent,
            text="Performance Metrics",
            style="AppleTitle.TLabel"
        )
        title.pack(anchor='w', pady=(0, 20))
        
        # Parse metrics
        metrics = {}
        for line in metrics_text.split('\n'):
            if ':' in line:
                metric, value = line.split(':', 1)
                metric = metric.strip().lower()
                value = value.strip()
                
                try:
                    value = value.replace('%', '')
                    value = float(value) / 100 if float(value) > 1 else float(value)
                except:
                    value = 0.0
                
                metrics[metric] = value
        
        # Display metrics
        metric_data = [
            ("Accuracy", metrics.get('accuracy', 0), APPLE_COLORS['success']),
            ("Precision", metrics.get('precision', 0), APPLE_COLORS['primary']),
            ("Recall", metrics.get('recall', 0), APPLE_COLORS['warning']),
            ("F1 Score", metrics.get('f1', 0), APPLE_COLORS['error'])
        ]
        
        for name, value, color in metric_data:
            # Metric container
            metric_frame = ttk.Frame(parent)
            metric_frame.pack(fill='x', pady=10)
            
            # Name
            name_label = ttk.Label(
                metric_frame,
                text=name,
                style="AppleBody.TLabel"
            )
            name_label.pack(anchor='w')
            
            # Value with color
            value_label = ttk.Label(
                metric_frame,
                text=f"{value:.1%}",
                font=(FONTS['system'][0], 24, 'bold'),
                foreground=color
            )
            value_label.pack(anchor='w', pady=(5, 0))