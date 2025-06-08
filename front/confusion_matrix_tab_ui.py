# front/confusion_matrix_tab_ui.py

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from backend.ConfusionMatrixManager import ConfusionMatrixManager
from backend.Evaluation import compute_confusion_matrix, compute_metrics
from backend.ImagePreprocessing import preprocess_image
from backend.Inference import predict_image
from front.config import APPLE_COLORS, FONTS, IMAGE_PREVIEW_SIZE
from front.drag_drop_handler import DropZone

class ConfusionMatrixTabUI:
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.manager = ConfusionMatrixManager()
        self.class_names = [
            "COVID-19", "Normal",
            "Pneumonia-Bacterial", "Pneumonia-Viral"
        ]
        self.matrix_displayed = False
        self._build_ui()

    def _build_ui(self):
        # Main container
        main_frame = ttk.Frame(self.parent, style="AppleMain.TFrame")
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Single card frame for all content
        self.content_frame = ttk.Frame(main_frame, style="AppleCard.TFrame")
        self.content_frame.pack(fill='both', expand=True)
        
        # Create both containers (switching between them)
        # Dataset selection container
        self.dataset_container = ttk.Frame(self.content_frame)
        self.dataset_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(
            self.dataset_container,
            text="Dataset Selection",
            style="AppleTitle.TLabel"
        )
        title_label.pack(anchor='w', pady=(0, 15))
        
        # Drop zone container
        self.drop_zone_container = ttk.Frame(self.dataset_container)
        self.drop_zone_container.pack(fill='both', expand=True)
        
        # Create initial drop zone
        self._create_drop_zone()
        
        # Evaluate button at bottom
        self.evaluate_btn = ttk.Button(
            self.dataset_container,
            text="Evaluate Model",
            command=self._on_evaluate,
            state='disabled',
            style="ApplePrimary.TButton"
        )
        self.evaluate_btn.pack(side='bottom', pady=(20, 0))
        
        # Progress indicators (hidden initially)
        self.progress_frame = ttk.Frame(self.dataset_container)
        
        self.progress = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=400,
            maximum=100,
            style="Apple.Horizontal.TProgressbar"
        )
        self.progress.pack()
        
        self.progress_label = ttk.Label(
            self.progress_frame,
            text="",
            style="AppleSecondary.TLabel"
        )
        self.progress_label.pack(pady=(5, 0))
        
        # Results container (hidden initially)
        self.results_container = ttk.Frame(self.content_frame)
        
        # Store dataset path
        self.dataset_path = None

    def _create_drop_zone(self):
        """Create or recreate drop zone"""
        # Clear existing widgets
        for widget in self.drop_zone_container.winfo_children():
            widget.destroy()
        
        self.drop_zone = DropZone(
            self.drop_zone_container,
            self._handle_dropped_folder,
            accept_folders=True,
            height=300
        )
        self.drop_zone.pack(fill='both', expand=True)

    def _show_dataset_info(self, folder_name):
        """Show dataset information in the drop zone area"""
        # Hide drop zone
        self.drop_zone.pack_forget()
        
        # Create info frame if it doesn't exist
        self.dataset_info_frame = ttk.Frame(self.drop_zone_container)
        
        # Clear any existing content
        for widget in self.dataset_info_frame.winfo_children():
            widget.destroy()
        
        # Create centered content
        center_frame = ttk.Frame(self.dataset_info_frame)
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Penguin with OK sign emoji
        penguin_label = ttk.Label(
            center_frame,
            text="🐧👌",
            font=(FONTS['system'][0], 64)
        )
        penguin_label.pack()
        
        # Dataset name
        name_label = ttk.Label(
            center_frame,
            text=folder_name,
            font=(FONTS['system'][0], 24, 'bold'),
            foreground=APPLE_COLORS['text_primary']
        )
        name_label.pack(pady=(20, 10))
        
        # Status
        status_label = ttk.Label(
            center_frame,
            text="Ready for evaluation",
            font=(FONTS['system'][0], 16),
            foreground=APPLE_COLORS['success']
        )
        status_label.pack()
        
        # Show the info frame
        self.dataset_info_frame.pack(fill='both', expand=True)

    def _handle_dropped_folder(self, folder_path):
        """Handle dropped folder"""
        if os.path.isdir(folder_path):
            self.dataset_path = folder_path
            folder_name = os.path.basename(folder_path)
            
            # Show dataset info
            self._show_dataset_info(folder_name)
            
            # Enable evaluate button
            self.evaluate_btn.config(state='normal')
            
            self.app.show_notification(f"Dataset folder selected: {folder_name}", "info")
        else:
            self.app.show_notification("Please select a valid folder", "error")

    def _reset_to_selection(self):
        """Reset to dataset selection view directly"""
        # Clear dataset path
        self.dataset_path = None
        
        # Hide results
        self.results_container.pack_forget()
        
        # Show dataset container
        self.dataset_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Recreate drop zone
        self._create_drop_zone()
        
        # Disable evaluate button
        self.evaluate_btn.config(state='disabled')
        
        self.matrix_displayed = False

    def _on_evaluate(self):
        """Start evaluation"""
        if not self.dataset_path:
            self.app.show_notification("Please select a dataset folder", "error")
            return
        
        sess = self.app.model_manager.get_current_model()
        if not sess:
            error_msg = "No model loaded. Please select a model first."
            self.app.show_notification(error_msg, "error")
            return
        
        # Check dataset structure
        missing_folders = []
        for class_name in self.class_names:
            class_path = os.path.join(self.dataset_path, class_name)
            if not os.path.isdir(class_path):
                missing_folders.append(class_name)
        
        if missing_folders:
            error_msg = f"Dataset missing folders: {', '.join(missing_folders)}"
            self.app.show_notification(error_msg, "error")
            return
        
        # Reset UI
        self.evaluate_btn.config(state='disabled')
        
        # Show progress
        self.progress_frame.pack(pady=(20, 0))
        self.progress['value'] = 0
        self.progress_label.config(text="Preparing evaluation...")
        
        # Start evaluation thread
        threading.Thread(target=self._run_evaluation, daemon=True).start()

    def _run_evaluation(self):
        """Run evaluation in background"""
        sess = self.app.model_manager.get_current_model()
        
        # Count files
        files = []
        for idx, cls in enumerate(self.class_names):
            folder = os.path.join(self.dataset_path, cls)
            if not os.path.isdir(folder):
                continue
            for fn in os.listdir(folder):
                if fn.lower().endswith(('.png', '.jpg', '.jpeg')):
                    files.append((idx, os.path.join(folder, fn)))
        
        total = len(files)
        if total == 0:
            self.app.root.after(0, lambda: self._evaluation_complete(None, None, "No images found in dataset"))
            return
        
        # Process images
        y_true, y_pred = [], []
        for i, (true_idx, path) in enumerate(files):
            try:
                tensor = preprocess_image(path)
                probs = predict_image(sess, tensor)
                pred_idx = int(probs.argmax())
            except Exception:
                pred_idx = 0
            
            y_true.append(true_idx)
            y_pred.append(pred_idx)
            
            # Update progress
            progress = int((i + 1) / total * 100)
            self.app.root.after(0, lambda p=progress, c=i+1, t=total: (
                self.progress.configure(value=p),
                self.progress_label.config(text=f"Processing images: {c}/{t}")
            ))
        
        # Compute confusion matrix and metrics
        cm = compute_confusion_matrix(y_true, y_pred, len(self.class_names))
        metrics = compute_metrics(cm)
        
        # Save confusion matrix with full dataset path
        img_path = self.manager.save_confusion_matrix(
            cm,
            self.class_names,
            self.app.model_manager.current_model_name,
            self.dataset_path  # Pass full path
        )
        
        # Complete
        self.app.root.after(0, lambda: self._evaluation_complete(metrics, img_path, None))

    def _evaluation_complete(self, metrics, img_path, error=None):
        """Handle evaluation completion"""
        # Hide progress
        self.progress_frame.pack_forget()
        self.evaluate_btn.config(state='normal')
        
        if error:
            self.app.show_notification(error, "error")
            return
        
        # Switch to results display
        self.dataset_container.pack_forget()
        
        # Clear and setup results container
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        results_content = ttk.Frame(self.results_container)
        results_content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(
            results_content,
            text="Evaluation Results",
            style="AppleTitle.TLabel"
        )
        title_label.pack(anchor='w', pady=(0, 20))
        
        # Create two columns layout
        content_frame = ttk.Frame(results_content)
        content_frame.pack(fill='both', expand=True)
        
        # Left column for matrix
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side='left', fill='both', expand=True)
        
        # Right column for metrics
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side='left', fill='both', expand=True, padx=(20, 0))
        
        # Display matrix
        self._display_matrix(left_frame, img_path)
        
        # Display metrics vertically
        self._display_metrics_vertical(right_frame, metrics)
        
        # Add hint at bottom
        hint_label = ttk.Label(
            results_content,
            text="Click the matrix to evaluate another dataset",
            style="AppleSecondary.TLabel"
        )
        hint_label.pack(pady=(20, 0))
        
        # Show results container
        self.results_container.pack(fill='both', expand=True, padx=20, pady=20)
        self.matrix_displayed = True
        
        # Update history
        self.app.cm_history_tab_ui._load_history()
        
        # Show success notification
        self.app.show_notification(
            f"Evaluation complete. Accuracy: {metrics['accuracy']:.2%}",
            "success"
        )

    def _display_matrix(self, parent, img_path):
        """Display confusion matrix with click handler"""
        if os.path.isfile(img_path):
            try:
                # Load image
                img = Image.open(img_path)
                
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
                
                # Display with click handler
                img_label = ttk.Label(img_container, image=photo, cursor="hand2")
                img_label.image = photo  # Keep reference
                img_label.pack()
                
                # Bind click to reset
                img_label.bind("<Button-1>", lambda e: self._reset_to_selection())
                
            except Exception as e:
                self.app.show_notification(f"Failed to display matrix: {str(e)}", "error")

    def _display_metrics_vertical(self, parent, metrics):
        """Display metrics vertically"""
        # Metrics title
        metrics_title = ttk.Label(
            parent,
            text="Performance Metrics",
            style="AppleTitle.TLabel"
        )
        metrics_title.pack(anchor='w', pady=(0, 20))
        
        metric_data = [
            ("Accuracy", metrics['accuracy'], APPLE_COLORS['success']),
            ("Precision", metrics['precision'], APPLE_COLORS['primary']),
            ("Recall", metrics['recall'], APPLE_COLORS['warning']),
            ("F1 Score", metrics['f1'], APPLE_COLORS['error'])
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