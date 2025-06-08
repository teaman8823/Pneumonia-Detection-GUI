# front/classify_tab_ui.py

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np

from front.config import ENABLE_DRAG_DROP, APPLE_COLORS, FONTS, IMAGE_PREVIEW_SIZE
from front.drag_drop_handler import DropZone, DragDropHandler
from backend.ImagePreprocessing import preprocess_image
from backend.Inference import predict_image

class ClassifyTabUI:
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.image_data = None
        self.current_path = ''
        self.preview_size = (IMAGE_PREVIEW_SIZE, IMAGE_PREVIEW_SIZE)
        self._build_ui()

    def _build_ui(self):
        # Main container
        main_frame = ttk.Frame(self.parent, style="AppleMain.TFrame")
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Content area with two columns
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True)
        
        # Left column - Image preview (fixed size)
        left_frame = ttk.Frame(content_frame, style="AppleCard.TFrame")
        left_frame.pack(side='left', fill='y', padx=(0, 10))
        
        # Fixed size container for image with gray background
        self.image_container = ttk.Frame(left_frame, style="AppleCard.TFrame")
        self.image_container.pack(padx=20, pady=20)
        
        # Gray background frame for image
        self.image_bg_frame = ttk.Frame(
            self.image_container,
            width=self.preview_size[0],
            height=self.preview_size[1],
            style="AppleCard.TFrame"
        )
        self.image_bg_frame.pack()
        self.image_bg_frame.pack_propagate(False)
        
        # Create drop zone
        self.drop_zone = DropZone(
            self.image_bg_frame,
            self._handle_dropped_file,
            accept_folders=False,
            width=self.preview_size[0],
            height=self.preview_size[1]
        )
        self.drop_zone.pack()
        
        # Image label (hidden initially)
        self.image_label = ttk.Label(self.image_bg_frame, anchor='center', cursor="hand2")
        
        # Add drag handler to the entire image container
        self.drag_handler = DragDropHandler(
            self.image_bg_frame,
            self._handle_dropped_file,
            file_types=[("Images", "*.png *.jpg *.jpeg")],
            accept_folders=False
        )
        
        # Right column - Results
        right_frame = ttk.Frame(content_frame, style="AppleCard.TFrame")
        right_frame.pack(side='left', fill='both', expand=True, padx=(10, 0))
        
        right_container = ttk.Frame(right_frame)
        right_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Results title
        results_title = ttk.Label(
            right_container,
            text="Analysis Results",
            style="AppleTitle.TLabel"
        )
        results_title.pack(anchor='w', pady=(0, 20))
        
        # Result display area
        self.result_frame = ttk.Frame(right_container)
        self.result_frame.pack(fill='both', expand=True)
        
        # Initial empty state
        self.empty_label = ttk.Label(
            self.result_frame,
            text="No analysis performed yet",
            style="AppleSecondary.TLabel"
        )
        self.empty_label.pack(expand=True)
        
        # Bottom button area
        button_frame = ttk.Frame(right_container)
        button_frame.pack(side='bottom', anchor='e', pady=(20, 0))
        
        # Analyze button (disabled initially)
        self.analyze_btn = ttk.Button(
            button_frame,
            text="Analyze",
            state='disabled',
            command=self._on_analyze,
            style="ApplePrimary.TButton"
        )
        self.analyze_btn.pack(side='left')
        
        # Progress bar (hidden initially)
        self.progress = ttk.Progressbar(
            right_container,
            mode='determinate',
            length=300,
            maximum=100,
            style="Apple.Horizontal.TProgressbar"
        )

    def _handle_dropped_file(self, file_path):
        """Handle dropped file - just load, don't analyze"""
        self._load_image(file_path)

    def _reset_to_drop_zone(self):
        """Reset to show drop zone"""
        self.clear_image_and_result()

    def _load_image(self, path):
        """Load and display image"""
        # Clear previous results
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        # Show loading state
        loading_label = ttk.Label(
            self.result_frame,
            text="Loading image...",
            style="AppleSecondary.TLabel"
        )
        loading_label.pack(expand=True)
        
        try:
            # Load image
            pil_img = Image.open(path)
            
            # Calculate size to fit in preview maintaining aspect ratio
            pil_img.thumbnail(self.preview_size, Image.Resampling.LANCZOS)
            
            # Create gray background
            bg = Image.new('RGB', self.preview_size, APPLE_COLORS['separator'])
            # Calculate position to center image
            x = (self.preview_size[0] - pil_img.width) // 2
            y = (self.preview_size[1] - pil_img.height) // 2
            
            # Convert to RGB if necessary
            if pil_img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', pil_img.size, (255, 255, 255))
                if pil_img.mode == 'P':
                    pil_img = pil_img.convert('RGBA')
                rgb_img.paste(pil_img, mask=pil_img.split()[-1] if pil_img.mode == 'RGBA' else None)
                pil_img = rgb_img
            
            # Paste image on gray background
            bg.paste(pil_img, (x, y))
            
            # Convert to PhotoImage
            tk_img = ImageTk.PhotoImage(bg)
            
            # Hide drop zone and show image
            self.drop_zone.pack_forget()
            self.image_label.configure(image=tk_img)
            self.image_label.image = tk_img
            self.image_label.pack(fill='both', expand=True)
            
            # Bind click event to reset
            self.image_label.bind("<Button-1>", lambda e: self._reset_to_drop_zone())
            
            # Show success notification
            self.app.show_notification(f"Image loaded: {os.path.basename(path)}", "success")
            
        except Exception as e:
            self.app.show_notification(f"Failed to load image: {str(e)}", "error")
            loading_label.config(text="Failed to load image")
            return
        
        # Preprocess image
        try:
            self.image_data = preprocess_image(path)
            self.current_path = path
            
            # Enable analyze button
            self.analyze_btn.config(state='normal')
            
            # Update status
            loading_label.config(text="Ready for analysis")
            
        except Exception as e:
            self.app.show_notification(f"Preprocessing failed: {str(e)}", "error")
            loading_label.config(text="Preprocessing failed")
            self.analyze_btn.config(state='disabled')

    def _on_analyze(self):
        """Execute analysis"""
        if self.image_data is None:
            return
        
        # Disable button
        self.analyze_btn.config(state='disabled')
        
        # Show progress
        self.progress.pack(side='bottom', fill='x', pady=(10, 0))
        self.progress['value'] = 0
        
        # Clear results
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        analyzing_label = ttk.Label(
            self.result_frame,
            text="Analyzing X-ray image...",
            style="AppleBody.TLabel"
        )
        analyzing_label.pack(expand=True)
        
        # Start analysis thread
        threading.Thread(target=self._predict, daemon=True).start()

    def _predict(self):
        """Run prediction in background"""
        sess = self.app.model_manager.get_current_model()
        if not sess:
            self.app.root.after(0, lambda: self._show_error("No model loaded"))
            return
        
        # Update progress
        self.app.root.after(0, lambda: self.progress.configure(value=30))
        
        try:
            probs = predict_image(sess, self.image_data)
        except Exception as e:
            self.app.root.after(0, lambda: self._show_error(f"Analysis failed: {str(e)}"))
            return
        
        # Update progress
        self.app.root.after(0, lambda: self.progress.configure(value=100))
        
        # Display results
        self.app.root.after(100, lambda: self._display(probs))

    def _display(self, probs):
        """Display prediction results"""
        names = ["COVID-19", "Normal", "Pneumonia-Bacterial", "Pneumonia-Viral"]
        
        # Find highest probability
        max_idx = int(probs.argmax())
        max_prob = probs[max_idx]
        max_name = names[max_idx]
        
        # Clear results area
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        # Main result display
        result_container = ttk.Frame(self.result_frame)
        result_container.pack(fill='both', expand=True)
        
        # Diagnosis section
        diagnosis_label = ttk.Label(
            result_container,
            text="Primary Diagnosis",
            style="AppleSecondary.TLabel"
        )
        diagnosis_label.pack(anchor='w')
        
        # Main result with transparent background
        result_text = ttk.Label(
            result_container,
            text=max_name,
            style="AppleValue.TLabel"
        )
        result_text.config(font=(FONTS['system'][0], 28, 'bold'))
        result_text.pack(anchor='w', pady=(5, 10))
        
        # Confidence level with transparent background
        confidence_label = ttk.Label(
            result_container,
            text=f"Confidence Level: {max_prob*100:.1f}%",
            style="AppleBody.TLabel"
        )
        confidence_label.config(font=(FONTS['system'][0], 18))
        confidence_label.pack(anchor='w', pady=(0, 10))
        
        # Visual confidence bar
        self._create_confidence_bar(result_container, max_prob)
        
        # Detailed probabilities
        detail_label = ttk.Label(
            result_container,
            text="Detailed Analysis",
            style="AppleSecondary.TLabel"
        )
        detail_label.pack(anchor='w', pady=(20, 5))
        
        # All probabilities with transparent background
        for name, prob in zip(names, probs):
            prob_text = f"{name}: {prob*100:.2f}%"
            
            prob_label = ttk.Label(
                result_container,
                text=prob_text,
                style="AppleSecondary.TLabel"
            )
            prob_label.pack(anchor='w', pady=2)
        
        # Model info
        model_label = ttk.Label(
            result_container,
            text=f"Model: {self.app.model_manager.current_model_name}",
            style="AppleSecondary.TLabel"
        )
        model_label.pack(anchor='w', pady=(15, 0))
        
        # Save to history
        full_results = "\n".join([f"{n}: {p*100:.2f}%" for n, p in zip(names, probs)])
        self.app.history_manager.add_entry(
            self.current_path,
            self.app.model_manager.current_model_name,
            max_name,
            full_results
        )
        self.app.history_tab_ui.update_history()
        
        # Hide progress and re-enable button
        self.progress.pack_forget()
        self.analyze_btn.config(state='normal')
        
        # Show notification
        self.app.show_notification(
            f"Analysis complete: {max_name} ({max_prob*100:.1f}%)",
            "success"
        )

    def _get_confidence_color(self, confidence):
        """Get color based on confidence level"""
        if confidence >= 0.9:
            return APPLE_COLORS['success']
        elif confidence >= 0.75:
            return APPLE_COLORS['warning']
        else:
            return APPLE_COLORS['error']

    def _create_confidence_bar(self, parent, confidence):
        """Create visual confidence bar"""
        bar_frame = ttk.Frame(parent)
        bar_frame.pack(fill='x', pady=(5, 0))
        
        canvas = tk.Canvas(
            bar_frame,
            height=8,
            bg=APPLE_COLORS['separator'],
            highlightthickness=0
        )
        canvas.pack(fill='x')
        
        def draw_bar(event=None):
            canvas.delete('all')
            width = canvas.winfo_width()
            if width > 1:
                # Background
                canvas.create_rectangle(
                    0, 0, width, 8,
                    fill=APPLE_COLORS['separator'],
                    outline=''
                )
                # Confidence bar
                bar_width = int(width * confidence)
                canvas.create_rectangle(
                    0, 0, bar_width, 8,
                    fill=self._get_confidence_color(confidence),
                    outline=''
                )
        
        canvas.bind('<Configure>', draw_bar)

    def _show_error(self, message):
        """Show error state"""
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        error_label = ttk.Label(
            self.result_frame,
            text=message,
            foreground=APPLE_COLORS['error'],
            style="AppleBody.TLabel"
        )
        error_label.pack(expand=True)
        
        self.progress.pack_forget()
        self.analyze_btn.config(state='normal')
        
        self.app.show_notification(message, "error")

    def clear_image_and_result(self):
        """Clear all content"""
        self.image_data = None
        self.current_path = ''
        
        # Show drop zone, hide image
        self.image_label.pack_forget()
        self.image_label.configure(image='')
        self.image_label.image = None
        
        # Recreate drop zone
        self.drop_zone.pack_forget()
        self.drop_zone = DropZone(
            self.image_bg_frame,
            self._handle_dropped_file,
            accept_folders=False,
            width=self.preview_size[0],
            height=self.preview_size[1]
        )
        self.drop_zone.pack()
        
        # Clear results
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        self.empty_label = ttk.Label(
            self.result_frame,
            text="No analysis performed yet",
            style="AppleSecondary.TLabel"
        )
        self.empty_label.pack(expand=True)
        
        # Disable analyze button
        self.analyze_btn.config(state='disabled')