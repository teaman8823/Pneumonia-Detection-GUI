# backend/HistoryManager.py

import os
import csv
import shutil
from datetime import datetime

class HistoryManager:
    HISTORY_DIR = 'history'
    IMAGES_DIR = os.path.join(HISTORY_DIR, 'images')
    CSV_PATH = os.path.join(HISTORY_DIR, 'records.csv')
    MAX_RECORDS = 10

    def __init__(self):
        os.makedirs(self.IMAGES_DIR, exist_ok=True)
        if not os.path.isfile(self.CSV_PATH):
            with open(self.CSV_PATH, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ImageName', 'Model', 'Result', 'Probabilities', 'Timestamp', 'Path'])

    def add_entry(self, image_path, model_name, result, probabilities):
        """Save a copy of the image and record its metadata in CSV."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        basename = os.path.basename(image_path)
        name, ext = os.path.splitext(basename)
        safe_time = timestamp.replace(' ', '_').replace(':', '-')
        new_name = f"{name}_{safe_time}{ext}"
        dest = os.path.join(self.IMAGES_DIR, new_name)
        shutil.copy2(image_path, dest)

        # Load existing records
        with open(self.CSV_PATH, 'r', newline='') as f:
            rows = list(csv.reader(f))
        header, records = rows[0], rows[1:]

        # Append new record
        records.append([new_name, model_name, result, probabilities, timestamp, dest])

        # Enforce max records
        if len(records) > self.MAX_RECORDS:
            oldest = records.pop(0)
            old_path = oldest[5]
            if os.path.isfile(old_path):
                os.remove(old_path)

        # Write back to CSV
        with open(self.CSV_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(records)

    def get_history(self):
        """Return list of history entries as dicts."""
        history = []
        with open(self.CSV_PATH, 'r', newline='') as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for row in reader:
                history.append({
                    'ImageName': row[0],
                    'Model': row[1],
                    'Result': row[2],
                    'Probabilities': row[3],
                    'Timestamp': row[4],
                    'Path': row[5]
                })
        return history

    def clear_history(self):
        """Delete all stored images and reset CSV."""
        for fname in os.listdir(self.IMAGES_DIR):
            path = os.path.join(self.IMAGES_DIR, fname)
            if os.path.isfile(path):
                os.remove(path)
        with open(self.CSV_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ImageName', 'Model', 'Result', 'Probabilities', 'Timestamp', 'Path'])
