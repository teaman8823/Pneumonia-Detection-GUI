# backend/ConfusionMatrixManager.py

import os
import csv
import shutil
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .Evaluation import compute_metrics

class ConfusionMatrixManager:
    HISTORY_DIR = 'confusion_history'
    IMAGES_DIR = os.path.join(HISTORY_DIR, 'images')
    CSV_PATH = os.path.join(HISTORY_DIR, 'records.csv')
    MAX_RECORDS = 10

    def __init__(self):
        os.makedirs(self.IMAGES_DIR, exist_ok=True)
        if not os.path.isdir(self.HISTORY_DIR):
            os.makedirs(self.HISTORY_DIR, exist_ok=True)
        if not os.path.isfile(self.CSV_PATH):
            with open(self.CSV_PATH, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['PNGName', 'Timestamp', 'Metrics', 'Model', 'Path', 'Dataset'])

    def save_confusion_matrix(self, cm, class_names, model_name, dataset_path):
        """Save confusion matrix image and record metadata in CSV."""
        metrics = compute_metrics(cm)
        metrics_text = (
            f"Accuracy:{metrics['accuracy']:.4f}\n"
            f"Precision:{metrics['precision']:.4f}\n"
            f"Recall:{metrics['recall']:.4f}\n"
            f"F1:{metrics['f1']:.4f}"
        )
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        png_name = f'confusion_{timestamp.replace(":", "-").replace(" ", "_")}.png'
        img_path = os.path.join(self.IMAGES_DIR, png_name)
        
        # Extract dataset name from path
        dataset_name = os.path.basename(dataset_path) if dataset_path else "Unknown"
        
        # plot confusion matrix
        fig, ax = plt.subplots()
        im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        ax.figure.colorbar(im, ax=ax)
        ax.set(
            xticks=list(range(len(class_names))),
            yticks=list(range(len(class_names))),
            xticklabels=class_names,
            yticklabels=class_names,
            ylabel='True',
            xlabel='Predicted',
            title='Confusion Matrix'
        )
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, str(cm[i, j]), ha='center', va='center')
        fig.tight_layout()
        fig.savefig(img_path)
        plt.close(fig)

        # Load existing CSV records
        with open(self.CSV_PATH, 'r', newline='') as f:
            rows = list(csv.reader(f))
        header, records = rows[0], rows[1:]
        
        # Add dataset column if not present (for backward compatibility)
        if len(header) < 6:
            header.append('Dataset')
            # Add empty dataset for existing records
            for record in records:
                if len(record) < 6:
                    record.append('Unknown')
        
        records.append([png_name, timestamp, metrics_text, model_name, img_path, dataset_name])

        # Enforce maximum record retention
        if len(records) > self.MAX_RECORDS:
            oldest = records.pop(0)
            old_path = oldest[4]
            if os.path.isfile(old_path):
                os.remove(old_path)

        # Write back to CSV
        with open(self.CSV_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(records)
        return img_path

    def load_history(self):
        """Return list of confusion matrix history records."""
        history = []
        with open(self.CSV_PATH, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)  # skip header
            for row in reader:
                record = {
                    'PNGName': row[0],
                    'Timestamp': row[1],
                    'Metrics': row[2],
                    'Model': row[3],
                    'Path': row[4]
                }
                # Add dataset if available
                if len(row) > 5:
                    record['Dataset'] = row[5]
                else:
                    record['Dataset'] = 'Unknown'
                history.append(record)
        return history

    def clear_history(self):
        """Delete all confusion matrix images and reset CSV."""
        for fname in os.listdir(self.IMAGES_DIR):
            path = os.path.join(self.IMAGES_DIR, fname)
            if os.path.isfile(path):
                os.remove(path)
        with open(self.CSV_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['PNGName', 'Timestamp', 'Metrics', 'Model', 'Path', 'Dataset'])