# front/image_cache.py

from collections import OrderedDict
import sys

class ImageCache:
    """Lightweight image cache for Raspberry Pi"""
    
    def __init__(self, max_size_mb=100, max_items=50):
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.max_items = max_items
        self.cache = OrderedDict()
        self.current_size = 0
    
    def _estimate_size(self, photo_image):
        """Estimate PhotoImage memory size"""
        try:
            # Rough estimation based on image dimensions
            width = photo_image.width()
            height = photo_image.height()
            # Assume 4 bytes per pixel (RGBA)
            return width * height * 4
        except:
            # Default size if estimation fails
            return 1024 * 1024  # 1MB
    
    def get(self, key):
        """Get image from cache"""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def put(self, key, photo_image):
        """Add image to cache"""
        # If already in cache, remove old version
        if key in self.cache:
            self.remove(key)
        
        # Estimate size
        size = self._estimate_size(photo_image)
        
        # Evict items if necessary
        while (self.current_size + size > self.max_size or 
               len(self.cache) >= self.max_items) and self.cache:
            self._evict_oldest()
        
        # Add to cache
        self.cache[key] = photo_image
        self.current_size += size
    
    def remove(self, key):
        """Remove specific item from cache"""
        if key in self.cache:
            photo = self.cache[key]
            size = self._estimate_size(photo)
            del self.cache[key]
            self.current_size -= size
    
    def _evict_oldest(self):
        """Remove least recently used item"""
        if self.cache:
            key, photo = self.cache.popitem(last=False)
            size = self._estimate_size(photo)
            self.current_size -= size
    
    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        self.current_size = 0
    
    def get_info(self):
        """Get cache statistics"""
        return {
            'items': len(self.cache),
            'size_mb': self.current_size / (1024 * 1024),
            'max_size_mb': self.max_size / (1024 * 1024)
        }