# front/drag_drop_handler.py

import tkinter as tk
from tkinter import filedialog
import os
from front.config import APPLE_COLORS, FONTS

class DragDropHandler:
    """Handles drag and drop functionality with fallback for Raspberry Pi"""
    
    def __init__(self, widget, callback, file_types=None, accept_folders=False):
        self.widget = widget
        self.callback = callback
        self.file_types = file_types or [("All files", "*.*")]
        self.accept_folders = accept_folders
        
        # Try to use tkinterdnd2 first
        self.use_tkdnd = False
        try:
            import tkinterdnd2
            self.use_tkdnd = True
            self._setup_tkdnd(tkinterdnd2)
        except Exception:
            # Fallback to pure Tkinter implementation
            self._setup_fallback()
    
    def _setup_tkdnd(self, tkinterdnd2):
        """Setup tkinterdnd2 drag and drop"""
        try:
            # Get the top-level window
            toplevel = self.widget.winfo_toplevel()
            
            # Make sure it's a TkinterDnD.Tk window
            if hasattr(toplevel, 'TkdndVersion'):
                self.widget.drop_target_register(tkinterdnd2.DND_FILES)
                self.widget.dnd_bind('<<Drop>>', self._on_tkdnd_drop)
                self.widget.dnd_bind('<<DragEnter>>', self._on_tkdnd_enter)
                self.widget.dnd_bind('<<DragLeave>>', self._on_tkdnd_leave)
            else:
                # Fallback if not a TkinterDnD window
                self.use_tkdnd = False
                self._setup_fallback()
        except Exception:
            self.use_tkdnd = False
            self._setup_fallback()
    
    def _setup_fallback(self):
        """Setup fallback drag and drop using file dialog"""
        # Make widget look draggable
        try:
            self.widget.configure(cursor="hand2")
        except:
            pass
        
        # Create drop zone indicator
        self.widget.bind('<Enter>', self._on_enter)
        self.widget.bind('<Leave>', self._on_leave)
        self.widget.bind('<Button-1>', self._on_click)
    
    def _on_tkdnd_drop(self, event):
        """Handle tkinterdnd2 drop event"""
        files = self.widget.tk.splitlist(event.data)
        for path in files:
            # Clean path (remove curly braces if present)
            path = path.strip('{}')
            if self.accept_folders and os.path.isdir(path):
                self.callback(path)
                break
            elif not self.accept_folders and os.path.isfile(path):
                self.callback(path)
                break
    
    def _on_tkdnd_enter(self, event):
        """Handle drag enter for visual feedback"""
        event.widget.config(cursor="target")
    
    def _on_tkdnd_leave(self, event):
        """Handle drag leave"""
        event.widget.config(cursor="")
    
    def _on_enter(self, event):
        """Mouse enter - show drop indication"""
        pass
    
    def _on_leave(self, event):
        """Mouse leave - remove drop indication"""
        pass
    
    def _on_click(self, event):
        """Click to open file/folder dialog as fallback"""
        if self.accept_folders:
            path = filedialog.askdirectory(title="Select Folder")
        else:
            path = filedialog.askopenfilename(
                title="Select File",
                filetypes=self.file_types
            )
        
        if path:
            self.callback(path)

class DropZone(tk.Frame):
    """Visual drop zone widget with fixed size"""
    
    def __init__(self, parent, callback, accept_folders=False, width=None, height=None, **kwargs):
        # Extract custom properties
        bg_color = kwargs.pop('bg', APPLE_COLORS['surface'])
        
        super().__init__(parent, **kwargs)
        
        self.callback = callback
        self.accept_folders = accept_folders
        self.fixed_width = width
        self.fixed_height = height
        
        self.configure(
            bg=bg_color,
            relief='flat',
            borderwidth=2,
            highlightthickness=0
        )
        
        # Set fixed size if provided
        if width and height:
            self.configure(width=width, height=height)
            self.pack_propagate(False)  # Prevent size changes
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(
            self,
            bg=bg_color,
            highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)
        
        # Draw content
        self.canvas.bind('<Configure>', self._draw_content)
        
        # Setup drag and drop - try tkinterdnd2 first
        self.use_tkdnd = False
        try:
            import tkinterdnd2
            # Check if parent window supports DnD
            toplevel = self.winfo_toplevel()
            if hasattr(toplevel, 'TkdndVersion'):
                self.drop_target_register(tkinterdnd2.DND_FILES)
                self.dnd_bind('<<Drop>>', self._on_drop)
                self.dnd_bind('<<DragEnter>>', self._on_drag_enter)
                self.dnd_bind('<<DragLeave>>', self._on_drag_leave)
                self.use_tkdnd = True
        except Exception:
            pass
        
        # Always setup click handler as fallback
        self.canvas.bind('<Button-1>', self._on_click)
        
        # Visual feedback state
        self.is_hovering = False
    
    def _on_drop(self, event):
        """Handle drop event"""
        files = self.tk.splitlist(event.data)
        for path in files:
            # Clean path
            path = path.strip('{}')
            if self.accept_folders and os.path.isdir(path):
                self.callback(path)
                break
            elif not self.accept_folders and os.path.isfile(path):
                self.callback(path)
                break
        self.is_hovering = False
        self._draw_content()
    
    def _on_drag_enter(self, event):
        """Handle drag enter"""
        self.is_hovering = True
        self._draw_content()
    
    def _on_drag_leave(self, event):
        """Handle drag leave"""
        self.is_hovering = False
        self._draw_content()
    
    def _on_click(self, event):
        """Click to open file/folder dialog"""
        file_types = [("Folders", "*")] if self.accept_folders else [("Images", "*.png *.jpg *.jpeg")]
        
        if self.accept_folders:
            path = filedialog.askdirectory(title="Select Folder")
        else:
            path = filedialog.askopenfilename(
                title="Select File",
                filetypes=file_types
            )
        
        if path:
            self.callback(path)
    
    def _draw_content(self, event=None):
        """Draw drop zone content"""
        self.canvas.delete('all')
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width > 1 and height > 1:
            # Use hover color if dragging
            border_color = APPLE_COLORS['primary'] if self.is_hovering else APPLE_COLORS['text_tertiary']
            
            # Draw dashed border
            self._create_dashed_rect(
                10, 10, width-10, height-10,
                dash=(8, 4),
                fill=border_color,
                width=2
            )
            
            # Draw icon
            cx, cy = width // 2, height // 2 - 20
            icon_color = APPLE_COLORS['primary'] if self.is_hovering else APPLE_COLORS['text_secondary']
            
            if self.accept_folders:
                # Folder icon
                self._draw_folder_icon(cx, cy, icon_color)
            else:
                # Upload icon
                self._draw_upload_icon(cx, cy, icon_color)
            
            # Text
            text = "Drop folder here or click to browse" if self.accept_folders else "Drop image here or click to browse"
            self.canvas.create_text(
                cx, cy + 50,
                text=text,
                font=(FONTS['system'][0], FONTS['body_medium']),
                fill=icon_color
            )
    
    def _draw_upload_icon(self, cx, cy, color):
        """Draw upload icon"""
        # Arrow up
        self.canvas.create_line(
            cx, cy - 20, cx, cy + 20,
            fill=color, width=3
        )
        self.canvas.create_polygon(
            cx - 10, cy - 10,
            cx, cy - 20,
            cx + 10, cy - 10,
            fill=color, outline=''
        )
        
        # Cloud base
        self.canvas.create_oval(
            cx - 30, cy + 10, cx - 10, cy + 30,
            fill=color, outline=''
        )
        self.canvas.create_oval(
            cx + 10, cy + 10, cx + 30, cy + 30,
            fill=color, outline=''
        )
        self.canvas.create_rectangle(
            cx - 20, cy + 20, cx + 20, cy + 30,
            fill=color, outline=''
        )
    
    def _draw_folder_icon(self, cx, cy, color):
        """Draw folder icon"""
        # Folder body
        self.canvas.create_rectangle(
            cx - 30, cy - 10, cx + 30, cy + 20,
            fill=color, outline=''
        )
        # Folder tab
        self.canvas.create_polygon(
            cx - 30, cy - 10,
            cx - 20, cy - 20,
            cx, cy - 20,
            cx + 10, cy - 10,
            fill=color, outline=''
        )
    
    def _create_dashed_rect(self, x1, y1, x2, y2, **kwargs):
        """Create dashed rectangle"""
        line_kwargs = kwargs.copy()
        if 'outline' in line_kwargs:
            del line_kwargs['outline']
        
        # Draw dashed lines
        self.canvas.create_line(x1, y1, x2, y1, **line_kwargs)
        self.canvas.create_line(x2, y1, x2, y2, **line_kwargs)
        self.canvas.create_line(x2, y2, x1, y2, **line_kwargs)
        self.canvas.create_line(x1, y2, x1, y1, **line_kwargs)