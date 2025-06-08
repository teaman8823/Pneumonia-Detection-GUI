# backend/Inference.py

import numpy as np

def predict_image(session, image_input):
    """
    Predict classification probabilities for a preprocessed image.

    Parameters
    ----------
    session : onnxruntime.InferenceSession
        ONNX Runtime session.
    image_input : numpy.ndarray
        Input tensor of shape (1, C, H, W), dtype float32.

    Returns
    -------
    numpy.ndarray
        Softmax probability vector for each class.
    """
    # Get input name for the session
    input_name = session.get_inputs()[0].name
    # Run inference
    outputs = session.run(None, {input_name: image_input})
    logits = outputs[0].flatten()
    # Compute softmax with numerical stability
    exp_logits = np.exp(logits - np.max(logits))
    probabilities = exp_logits / np.sum(exp_logits)
    return probabilities
