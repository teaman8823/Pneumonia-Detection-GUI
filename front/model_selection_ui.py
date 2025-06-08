# front/model_selection_ui.py

import os
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from backend.ModelManager import ModelManager
from front.config import APPLE_COLORS, FONTS

class ModelSelectionUI:
    def __init__(self, app):
        """
        :param app: Main AppUI instance
        """
        self.app = app
        self.models_dir = ModelManager.MODELS_DIR
        self.persist_file = os.path.join(self.models_dir, "selected_model.csv")
        self._build_ui()
        
        # Auto-load models after UI is built
        self.app.root.after(100, self._auto_load_models)

    def _build_ui(self):
        # Top panel with Apple card style - removed bottom padding
        top_frame = ttk.Frame(self.app.main_container, style="AppleCard.TFrame")
        top_frame.pack(fill='x')  # No pady to save vertical space
        
        # Container with padding
        container = ttk.Frame(top_frame)
        container.pack(fill='x', padx=20, pady=16)
        
        # Model label
        model_label = ttk.Label(
            container, 
            text="Model:", 
            style="AppleBody.TLabel"
        )
        model_label.pack(side='left', padx=(0, 12))

        # Model dropdown with Apple style
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            container, 
            textvariable=self.model_var,
            state='readonly', 
            width=40,
            style="Apple.TCombobox"
        )
        self.model_combo.pack(side='left', padx=(0, 20))
        self.model_combo.bind('<<ComboboxSelected>>', self._on_selected)
        
        # Button container
        btn_container = ttk.Frame(container)
        btn_container.pack(side='left')

        # Import button
        import_btn = ttk.Button(
            btn_container, 
            text="Import Model", 
            command=self._import_model,
            style="AppleSecondary.TButton"
        )
        import_btn.pack(side='left', padx=(0, 12))

        # Remove button
        remove_btn = ttk.Button(
            btn_container, 
            text="Remove Model", 
            command=self._remove_model,
            style="AppleSecondary.TButton"
        )
        remove_btn.pack(side='left')
        
        # Status label
        self.status_label = ttk.Label(
            container,
            text="",
            style="AppleSecondary.TLabel"
        )
        self.status_label.pack(side='left', padx=(20, 0))

    def _auto_load_models(self):
        """Auto-load models from registry"""
        # First scan for models in the models directory
        self._scan_and_register_models()
        
        # Then refresh the list
        self._refresh_model_list()
        
        # Load last selected model
        if os.path.isfile(self.persist_file):
            try:
                with open(self.persist_file, 'r', newline='') as f:
                    rows = list(csv.reader(f))
                    if len(rows) > 1:
                        last_model = rows[-1][0]
                        if last_model in self.model_combo['values']:
                            self.model_var.set(last_model)
                            # Actually load the model
                            self._load_selected_model(last_model)
            except Exception:
                pass

    def _scan_and_register_models(self):
        """Scan models directory and register any unregistered models"""
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
            return
        
        # Get list of ONNX files
        onnx_files = [f for f in os.listdir(self.models_dir) 
                      if f.endswith('.onnx')]
        
        # Register any that aren't already registered
        for onnx_file in onnx_files:
            model_path = os.path.join(self.models_dir, onnx_file)
            model_name = os.path.splitext(onnx_file)[0]
            
            # Check if already registered
            if model_name not in self.app.model_manager.get_model_names():
                try:
                    self.app.model_manager.register_and_load_model(model_path)
                except Exception as e:
                    print(f"Failed to register {model_name}: {e}")

    def _refresh_model_list(self):
        """Refresh combobox values and set default selection"""
        models = self.app.model_manager.get_model_names()
        self.model_combo['values'] = models
        
        if models:
            # Pick first if current not valid
            sel = self.model_var.get()
            if not sel or sel not in models:
                sel = models[0]
                self.model_var.set(sel)
            # Apply selection
            self.app.model_manager.set_current_model(sel)
            self._persist_selection(sel)
            self._update_status(f"Model loaded: {sel}")
        else:
            self.model_var.set('')
            self.app.model_manager.current_model_name = None
            self._update_status("No models available")

    def _load_selected_model(self, model_name):
        """Load the selected model"""
        try:
            self.app.model_manager.set_current_model(model_name)
            if self.app.model_manager.ensure_model_loaded(model_name):
                self._update_status(f"Model loaded: {model_name}")
                self.app.show_notification(f"Model loaded: {model_name}", "success")
            else:
                self._update_status(f"Failed to load: {model_name}")
                self.app.show_notification(f"Failed to load model: {model_name}", "error")
        except Exception as e:
            self._update_status(f"Error: {str(e)}")
            self.app.show_notification(f"Model error: {str(e)}", "error")

    def _persist_selection(self, model_name):
        """Append the chosen model to selected_model.csv"""
        try:
            os.makedirs(self.models_dir, exist_ok=True)
            with open(self.persist_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([model_name])
        except Exception:
            pass

    def _on_selected(self, event=None):
        """User explicitly changed the combobox"""
        name = self.model_var.get()
        if name:
            self._load_selected_model(name)
            self._persist_selection(name)
            # Clear classify tab to avoid result confusion
            self.app.tabs_ui.clear_image_and_result()

    def _import_model(self):
        """Import new ONNX model"""
        path = filedialog.askopenfilename(
            title="Select ONNX Model",
            filetypes=[("ONNX Model", "*.onnx"), ("All files", "*.*")]
        )
        if not path:
            return
        
        try:
            self._update_status("Importing model...")
            imported_name = self.app.model_manager.import_model(path)
            self._refresh_model_list()
            # Select the newly imported model
            self.model_var.set(imported_name)
            self._load_selected_model(imported_name)
            self.app.show_notification(f"Model imported: {imported_name}", "success")
        except Exception as e:
            self.app.show_notification(f"Import failed: {str(e)}", "error")
            self._update_status("Import failed")

    def _remove_model(self):
        """Remove selected model"""
        name = self.model_var.get()
        if not name:
            self.app.show_notification("No model selected", "warning")
            return
        
        # Confirmation dialog with Apple style
        result = messagebox.askyesno(
            "Remove Model",
            f"Are you sure you want to remove '{name}' from the model list?\n\n"
            "The model file will remain in the models directory.",
            parent=self.app.root
        )
        
        if result:
            self.app.model_manager.remove_model(name)
            self._refresh_model_list()
            self.app.show_notification(f"Model removed: {name}", "info")

    def _update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)
        # Auto-clear after 3 seconds
        self.app.root.after(3000, lambda: self.status_label.config(text=""))