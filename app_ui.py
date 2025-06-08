# app_ui.py

import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
import os
import configparser

from front.config import ENABLE_FULLSCREEN, DEFAULT_THEME, APPLE_COLORS, ENABLE_ANIMATIONS
from backend.ModelManager import ModelManager
from backend.HistoryManager import HistoryManager
from front.model_selection_ui import ModelSelectionUI
from front.tabs_ui import TabsUI
from front.apple_styles import AppleStyleManager
from front.notification_system import NotificationManager

class AppUI:
    def __init__(self):
        # Load window state before creating window
        self.config_file = os.path.join(os.path.expanduser("~"), ".pneumonia_detection_config.ini")
        self.config = configparser.ConfigParser()
        self._load_config()
        
        # Create main window with theme
        self.root = ThemedTk(theme=DEFAULT_THEME)
        self.root.title("Pneumonia Detection")
        
        # Apply saved window geometry
        self._apply_window_state()
        
        # Initialize Apple style manager
        self.style_manager = AppleStyleManager(self.root)
        self.style_manager.apply_apple_styles()
        
        # Initialize notification system
        self.notification_manager = NotificationManager(self.root)
        
        # Configure window properties
        self.root.configure(bg=APPLE_COLORS['background'])
        self.root.minsize(800, 600)
        
        # Bind window state save on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.bind("<Configure>", self._on_window_configure)
        
        # Backend managers
        self.model_manager = ModelManager()
        self.history_manager = HistoryManager()
        
        # Create main container with padding
        self.main_container = ttk.Frame(self.root, style="AppleMain.TFrame")
        self.main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Top panel: model selection with Apple styling
        self.model_selection_ui = ModelSelectionUI(self)
        
        # Tabs for functionalities with Apple styling
        self.tabs_ui = TabsUI(self)
        self.history_tab_ui = self.tabs_ui.image_history_tab_ui
        self.cm_history_tab_ui = self.tabs_ui.eval_hist_tab_ui
        
        # Enable/disable animations based on config
        if hasattr(self, 'notification_manager'):
            self.notification_manager.enable_animations = ENABLE_ANIMATIONS

    def _load_config(self):
        """Load saved configuration"""
        try:
            self.config.read(self.config_file)
        except Exception:
            pass
    
    def _save_config(self):
        """Save current configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                self.config.write(f)
        except Exception:
            pass
    
    def _apply_window_state(self):
        """Apply saved window geometry and state"""
        try:
            if 'Window' in self.config:
                geometry = self.config.get('Window', 'geometry', fallback='1600x900')
                state = self.config.get('Window', 'state', fallback='normal')
                
                # Validate geometry against current screen
                self.root.update_idletasks()
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                
                # Parse geometry string
                import re
                match = re.match(r'(\d+)x(\d+)\+(-?\d+)\+(-?\d+)', geometry)
                if match:
                    w, h, x, y = map(int, match.groups())
                    # Ensure window is on screen
                    if x < 0 or x + w > screen_width:
                        x = (screen_width - w) // 2
                    if y < 0 or y + h > screen_height:
                        y = (screen_height - h) // 2
                    geometry = f"{w}x{h}+{x}+{y}"
                
                self.root.geometry(geometry)
                
                if state == 'zoomed' and not ENABLE_FULLSCREEN:
                    self.root.state('zoomed')
            else:
                self.root.geometry("1600x900")
                self.root.update_idletasks()
                # Center window
                w = self.root.winfo_width()
                h = self.root.winfo_height()
                x = (self.root.winfo_screenwidth() - w) // 2
                y = (self.root.winfo_screenheight() - h) // 2
                self.root.geometry(f"{w}x{h}+{x}+{y}")
                
        except Exception:
            self.root.geometry("1600x900")
        
        if ENABLE_FULLSCREEN:
            self.root.attributes('-fullscreen', True)
    
    def _on_window_configure(self, event=None):
        """Save window state on configuration change"""
        if event and event.widget == self.root:
            if not hasattr(self, '_save_timer'):
                self._save_timer = None
            
            # Cancel previous save timer
            if self._save_timer:
                self.root.after_cancel(self._save_timer)
            
            # Save after 1 second of no changes
            self._save_timer = self.root.after(1000, self._save_window_state)
    
    def _save_window_state(self):
        """Save current window geometry and state"""
        try:
            if 'Window' not in self.config:
                self.config['Window'] = {}
            
            self.config['Window']['geometry'] = self.root.geometry()
            self.config['Window']['state'] = self.root.state()
            self._save_config()
        except Exception:
            pass
    
    def _on_closing(self):
        """Handle window closing"""
        self._save_window_state()
        self.root.destroy()
    
    def show_notification(self, message, notification_type="info", duration=700):
        """Show Apple-style notification"""
        if hasattr(self, 'notification_manager'):
            self.notification_manager.show_notification(message, notification_type, duration)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AppUI()
    app.run()