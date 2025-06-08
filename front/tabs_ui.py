# front/tabs_ui.py

import tkinter as tk
from tkinter import ttk
from front.classify_tab_ui import ClassifyTabUI
from front.history_tab_ui import HistoryTabUI
from front.confusion_matrix_tab_ui import ConfusionMatrixTabUI
from front.confusion_matrix_history_tab_ui import ConfusionMatrixHistoryTabUI
from front.config import APPLE_COLORS, FONTS

class TabsUI:
    def __init__(self, app):
        """
        :param app: Main AppUI instance
        """
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Create the notebook for tabs with Apple style
        self.notebook = ttk.Notebook(self.app.main_container, style="Apple.TNotebook")
        self.notebook.pack(fill='both', expand=True)
        
        # Tab 1: Image Classify
        self.classify_frame = ttk.Frame(self.notebook, style="AppleMain.TFrame")
        self.notebook.add(self.classify_frame, text="Classify")
        self.classify_tab_ui = ClassifyTabUI(self.app, self.classify_frame)
        
        # Tab 2: Image History
        self.image_history_frame = ttk.Frame(self.notebook, style="AppleMain.TFrame")
        self.notebook.add(self.image_history_frame, text="History")
        self.image_history_tab_ui = HistoryTabUI(self.app, self.image_history_frame)
        
        # Tab 3: Evaluate Model
        self.eval_frame = ttk.Frame(self.notebook, style="AppleMain.TFrame")
        self.notebook.add(self.eval_frame, text="Evaluate")
        self.evaluate_tab_ui = ConfusionMatrixTabUI(self.app, self.eval_frame)
        
        # Tab 4: Evaluate Model History
        self.eval_hist_frame = ttk.Frame(self.notebook, style="AppleMain.TFrame")
        self.notebook.add(self.eval_hist_frame, text="Evaluation History")
        self.eval_hist_tab_ui = ConfusionMatrixHistoryTabUI(self.app, self.eval_hist_frame)
        
        # Equalize tab widths and center their labels
        self.notebook.bind('<Configure>', self._resize_tabs)
        
        # Set initial tab
        self.notebook.select(0)

    def _resize_tabs(self, event):
        """Resize tabs to be equal width"""
        if event.widget == self.notebook:
            total_width = event.width
            tabs = self.notebook.tabs()
            count = len(tabs)
            if count > 0 and total_width > 0:
                width = total_width // count
                style = ttk.Style()
                # Set each tab to fixed width and center its text
                style.configure('Apple.TNotebook.Tab', 
                    width=width, 
                    anchor='center',
                    justify='center'
                )

    def clear_image_and_result(self):
        """Clear the image preview and result text in the Classify tab"""
        self.classify_tab_ui.clear_image_and_result()