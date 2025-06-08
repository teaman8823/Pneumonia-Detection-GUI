# backend/ModelManager.py

import onnxruntime
import os
import shutil
import json
import hashlib
from datetime import datetime
from collections import OrderedDict

class ModelManager:
    MODELS_DIR = "models"
    REGISTRY_FILE = os.path.join(MODELS_DIR, "model_registry.json")
    MAX_LOADED_MODELS = 2  # Maximum models to keep in memory

    def __init__(self):
        os.makedirs(self.MODELS_DIR, exist_ok=True)
        self.models = OrderedDict()  # ONNX sessions (LRU cache)
        self.model_registry = {}     # Model metadata
        self.current_model_name = None
        
        # Load registry
        self._load_registry()

    def _load_registry(self):
        """Load model registry from file"""
        if os.path.isfile(self.REGISTRY_FILE):
            try:
                with open(self.REGISTRY_FILE, 'r') as f:
                    self.model_registry = json.load(f)
            except Exception:
                self.model_registry = {}
        else:
            self.model_registry = {}

    def _save_registry(self):
        """Save model registry to file"""
        try:
            with open(self.REGISTRY_FILE, 'w') as f:
                json.dump(self.model_registry, f, indent=2)
        except Exception:
            pass

    def _calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def register_and_load_model(self, file_path):
        """Register a model and optionally load it"""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Model file not found: {file_path}")
        
        basename = os.path.basename(file_path)
        model_name = os.path.splitext(basename)[0]
        
        # Check if already registered
        if model_name not in self.model_registry:
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Register model
            self.model_registry[model_name] = {
                'path': file_path,
                'name': model_name,
                'hash': file_hash,
                'registered_at': datetime.now().isoformat(),
                'last_used': None,
                'use_count': 0
            }
            self._save_registry()
        
        return model_name

    def import_model(self, file_path):
        """Copy ONNX file into models/ and register it"""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Model file not found: {file_path}")
        
        basename = os.path.basename(file_path)
        dest = os.path.join(self.MODELS_DIR, basename)
        
        # Copy file if not already in models directory
        if os.path.abspath(file_path) != os.path.abspath(dest):
            shutil.copy2(file_path, dest)
        
        # Register and return name
        return self.register_and_load_model(dest)

    def load_model(self, model_name):
        """Load model into memory"""
        if model_name in self.models:
            # Move to end (LRU)
            self.models.move_to_end(model_name)
            return self.models[model_name]
        
        if model_name not in self.model_registry:
            raise ValueError(f"Model not registered: {model_name}")
        
        model_info = self.model_registry[model_name]
        model_path = model_info['path']
        
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Check cache size and evict if necessary
        while len(self.models) >= self.MAX_LOADED_MODELS:
            # Remove least recently used
            oldest_name, oldest_session = self.models.popitem(last=False)
            del oldest_session
        
        # Load model
        try:
            session = onnxruntime.InferenceSession(model_path)
            session._model_path = model_path
            self.models[model_name] = session
            
            # Update usage stats
            self.model_registry[model_name]['last_used'] = datetime.now().isoformat()
            self.model_registry[model_name]['use_count'] += 1
            self._save_registry()
            
            return session
        except Exception as e:
            raise RuntimeError(f"Failed to load model {model_name}: {str(e)}")

    def ensure_model_loaded(self, model_name):
        """Ensure model is loaded, loading if necessary"""
        try:
            self.load_model(model_name)
            return True
        except Exception:
            return False

    def get_model_names(self):
        """Return list of registered model names"""
        return list(self.model_registry.keys())

    def set_current_model(self, model_name):
        """Set the active model"""
        if model_name in self.model_registry:
            self.current_model_name = model_name

    def get_current_model(self):
        """Return the currently active ONNX session, loading if necessary"""
        if not self.current_model_name:
            return None
        
        try:
            return self.load_model(self.current_model_name)
        except Exception:
            return None

    def remove_model(self, model_name):
        """Remove a model from registry (file remains)"""
        # Remove from loaded models
        if model_name in self.models:
            del self.models[model_name]
        
        # Remove from registry
        if model_name in self.model_registry:
            del self.model_registry[model_name]
            self._save_registry()
        
        # Clear current if it was removed
        if self.current_model_name == model_name:
            self.current_model_name = None

    def get_model_info(self, model_name):
        """Get detailed information about a model"""
        return self.model_registry.get(model_name, {})

    def cleanup_orphaned_models(self):
        """Remove registry entries for models whose files no longer exist"""
        orphaned = []
        for name, info in self.model_registry.items():
            if not os.path.isfile(info['path']):
                orphaned.append(name)
        
        for name in orphaned:
            self.remove_model(name)
        
        return orphaned