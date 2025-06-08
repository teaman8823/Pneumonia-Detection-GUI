# backend/ImagePreprocessing.py

import cv2
import numpy as np
import os

def preprocess_image(file_path):
    """
    Load and preprocess an image for model inference.
    Steps:
      1. Verify extension (.jpg/.jpeg/.png).
      2. Read image in BGR color.
      3. Resize to 256×256.
      4. Scale pixel values to [0,1].
      5. Normalize using ImageNet mean/std.
      6. Convert HWC→CHW and add batch dim → (1,3,256,256).
    Returns:
      numpy.ndarray of dtype float32.
    Raises:
      ValueError on load or resize failure.
    """
    valid_exts = {".jpg", ".jpeg", ".png"}
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext not in valid_exts:
        raise ValueError(f"Unsupported extension '{ext}'. Use JPG or PNG.")
    
    image = cv2.imread(file_path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot load image at '{file_path}'.")
    
    try:
        image = cv2.resize(image, (256, 256))
    except Exception as e:
        raise ValueError(f"Resize failed: {e}")
    
    image = image.astype(np.float32) / 255.0
    # HWC → CHW
    image = image.transpose(2, 0, 1)
    
    # ImageNet normalization
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3,1,1)
    std  = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3,1,1)
    image = (image - mean) / std
    
    # Add batch dimension
    return np.expand_dims(image, axis=0)
