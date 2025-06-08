import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from backend.Evaluation import evaluate_model, display_evaluation_results
from backend.ConfusionMatrixManager import ConfusionMatrixManager

class EvaluateTabUI:
    def __init__(self, app, parent):
        """
        :param app: Main AppUI instance
        :param parent: Frame for this tab
        """
        self.app = app
        self.parent = parent
        self.manager = ConfusionMatrixManager()
        self.class_names = [
            "COVID-19",
            "Normal",
            "Pneumonia-Bacterial",
            "Pneumonia-Viral"
        ]
        self._build_ui()

    def _build_ui(self):
        ctrl = ttk.Frame(self.parent)
        ctrl.pack(fill='x', padx=5, pady=5)

        ttk.Label(ctrl, text="Dataset Folder:").pack(side='left', padx=5)
        self.dataset_path_var = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.dataset_path_var, width=50).pack(side='left', padx=5)
        ttk.Button(ctrl, text="Browse", command=self._select_folder).pack(side='left', padx=5)
        self.eval_btn = ttk.Button(ctrl, text="Evaluate", command=self._on_evaluate)
        self.eval_btn.pack(side='left', padx=5)

        # Progress bar and percentage label (hidden initially)
        self.progress = ttk.Progressbar(ctrl, mode='determinate', length=200, maximum=100)
        self.percent_lbl = ttk.Label(ctrl, text="0%")
        self.progress.pack_forget()
        self.percent_lbl.pack_forget()

        # Output text box
        text_container = ttk.Frame(self.parent)
        text_container.pack(fill='both', expand=True, padx=5, pady=5)
        self.output_text = tk.Text(text_container, height=10, wrap='none')
        vsb = ttk.Scrollbar(text_container, orient='vertical', command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.output_text.pack(side='left', fill='both', expand=True)
        self.output_text.config(state='disabled')

    def _select_folder(self):
        folder = filedialog.askdirectory(title="Select Dataset Folder")
        if folder:
            self.dataset_path_var.set(folder)

    def _on_evaluate(self):
        folder = self.dataset_path_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("No folder", "Please select a valid dataset folder.")
            return
        model_session = self.app.model_manager.get_current_model()
        if not model_session:
            messagebox.showerror("Error", "No model loaded.")
            return

        # Prepare UI
        self.eval_btn.config(state='disabled')
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', 'end')
        self.output_text.config(state='disabled')
        self.progress.pack(side='left', padx=5)
        self.percent_lbl.pack(side='left', padx=5)
        self.progress['value'] = 0
        self.percent_lbl.config(text="0%")

        threading.Thread(
            target=self._evaluate_thread,
            args=(folder, model_session),
            daemon=True
        ).start()

    def _evaluate_thread(self, folder, model_session):
        # Run evaluation
        cm, metrics = evaluate_model(model_session, folder, self.class_names)

        # Update progress to 100%
        self.app.root.after(
            0,
            lambda: (
                self.progress.config(value=100),
                self.percent_lbl.config(text="100%")
            )
        )

        # Prepare report text
        report = display_evaluation_results((cm, metrics))

        # Display report in UI
        self.app.root.after(0, lambda: self._display_report(report))

        # Save confusion matrix image to history
        self.manager.save_confusion_matrix(
            cm,
            self.class_names,
            os.path.basename(model_session._model_path),
            os.path.basename(folder)
        )

        # Finish up UI reset
        self.app.root.after(0, self._finish_evaluate)

    def _display_report(self, report: str):
        self.output_text.config(state='normal')
        self.output_text.insert('1.0', report)
        self.output_text.config(state='disabled')

    def _finish_evaluate(self):
        self.progress.pack_forget()
        self.percent_lbl.pack_forget()
        self.eval_btn.config(state='normal')
