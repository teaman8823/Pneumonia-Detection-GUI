# backend/Evaluation.py

import os
import queue
import threading
import warnings
from typing import Dict, List, Tuple

import numpy as np

from .ImagePreprocessing import preprocess_image
from .Inference import predict_image

# Special token to signal the end of loading images
STOP_TOKEN = object()

def compute_confusion_matrix(y_true: List[int],
                             y_pred: List[int],
                             num_classes: int) -> np.ndarray:
    """
    Compute a confusion matrix as a 2D numpy array.
    """
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1
    return cm

def compute_metrics(cm: np.ndarray) -> Dict[str, float]:
    """
    Compute accuracy, macro‑precision, macro‑recall, macro‑F1 from the confusion matrix.
    """
    true_positives = np.diag(cm).astype(np.float64)
    total = cm.sum()
    accuracy = float(np.sum(true_positives) / total) if total > 0 else 0.0

    support = cm.sum(axis=1).astype(np.float64)
    predicted = cm.sum(axis=0).astype(np.float64)
    with np.errstate(divide='ignore', invalid='ignore'):
        precision = np.where(predicted > 0, true_positives/predicted, 0.0)
        recall    = np.where(support > 0, true_positives/support, 0.0)
    f1 = np.where((precision + recall) > 0,
                  2 * precision * recall / (precision + recall),
                  0.0)
    return {
        'accuracy': accuracy,
        'precision': float(np.mean(precision)),
        'recall': float(np.mean(recall)),
        'f1': float(np.mean(f1))
    }

def display_evaluation_results(results: Tuple[np.ndarray, Dict[str, float]]) -> str:
    """
    Return a formatted string of metrics and confusion matrix.
    """
    cm, metrics = results
    lines = ["Evaluation Metrics:"]
    for k, v in metrics.items():
        lines.append(f"{k}: {v:.4f}")
    lines.append("")  # blank line
    lines.append("Confusion Matrix:")
    for row in cm:
        lines.append(" ".join(str(x) for x in row))
    return "\n".join(lines)

def evaluate_model(session,
                   dataset_path: str,
                   class_names: List[str],
                   queue_size: int = 4) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Evaluate model on images under dataset_path/class_name folders.
    Returns (confusion_matrix, metrics_dict).
    """
    valid_exts = ('.jpg', '.jpeg', '.png')
    num_classes = len(class_names)

    img_queue: queue.Queue = queue.Queue(maxsize=queue_size)

    def loader():
        for idx, cls in enumerate(class_names):
            folder = os.path.join(dataset_path, cls)
            if not os.path.isdir(folder):
                warnings.warn(f"Missing folder: {folder}")
                continue
            for fname in os.listdir(folder):
                if not fname.lower().endswith(valid_exts):
                    continue
                path = os.path.join(folder, fname)
                try:
                    tensor = preprocess_image(path)
                    img_queue.put((idx, tensor))
                except Exception as e:
                    warnings.warn(f"[Skip] {path}: {e}")
        img_queue.put(STOP_TOKEN)

    threading.Thread(target=loader, daemon=True).start()

    y_true, y_pred = [], []

    while True:
        item = img_queue.get()
        if item is STOP_TOKEN:
            break
        true_idx, tensor = item
        try:
            probs = predict_image(session, tensor)
            pred_idx = int(np.argmax(probs))
        except Exception:
            pred_idx = 0
        y_true.append(true_idx)
        y_pred.append(pred_idx)

    cm = compute_confusion_matrix(y_true, y_pred, num_classes)
    metrics = compute_metrics(cm)
    return cm, metrics
