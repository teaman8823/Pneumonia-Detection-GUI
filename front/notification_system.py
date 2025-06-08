# front/notification_system.py

import tkinter as tk
from tkinter import ttk
import time
import threading
from queue import Queue
from front.config import APPLE_COLORS, FONTS, CORNER_RADIUS, ANIMATION_DURATION, ANIMATION_FPS, NOTIFICATION_DURATION

class NotificationWidget(tk.Toplevel):
    """Apple-style notification widget"""
    
    def __init__(self, parent, message, notification_type="info", duration=NOTIFICATION_DURATION):
        super().__init__(parent)
        
        self.parent = parent
        self.message = message
        self.notification_type = notification_type
        self.duration = duration
        self.is_expanded = False
        self.is_paused = False
        
        # Configure window
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.configure(bg=APPLE_COLORS['surface'])
        
        # Make window transparent on Linux (Raspberry Pi)
        try:
            self.attributes('-alpha', 0.95)
        except:
            pass
        
        # Get colors based on type
        colors = {
            'success': APPLE_COLORS['success'],
            'error': APPLE_COLORS['error'],
            'warning': APPLE_COLORS['warning'],
            'info': APPLE_COLORS['primary']
        }
        self.accent_color = colors.get(notification_type, APPLE_COLORS['primary'])
        
        # Create content
        self._create_content()
        
        # Position window
        self._position_window()
        
        # Bind click events
        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        
        # Start animation
        self.animation_progress = 0.0
        self.animation_direction = 1  # 1 for in, -1 for out
        self._animate()
    
    def _create_content(self):
        """Create notification content"""
        # Main container
        container = tk.Frame(self, bg=APPLE_COLORS['surface'])
        container.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Color accent bar
        accent_bar = tk.Frame(container, bg=self.accent_color, width=4)
        accent_bar.pack(side='left', fill='y')
        
        # Content frame
        content = tk.Frame(container, bg=APPLE_COLORS['surface'])
        content.pack(side='left', fill='both', expand=True, padx=16, pady=12)
        
        # Icon label (using Unicode symbols)
        icons = {
            'success': '\u2713',  # Checkmark
            'error': '\u2717',    # X mark
            'warning': '\u26A0',  # Warning triangle
            'info': '\u2139'      # Info circle
        }
        icon = icons.get(self.notification_type, '')
        
        icon_label = tk.Label(
            content,
            text=icon,
            font=('Arial', 20),
            fg=self.accent_color,
            bg=APPLE_COLORS['surface']
        )
        icon_label.pack(side='left', padx=(0, 12))
        
        # Message frame
        message_frame = tk.Frame(content, bg=APPLE_COLORS['surface'])
        message_frame.pack(side='left', fill='both', expand=True)
        
        # Message label (truncated by default)
        self.message_label = tk.Label(
            message_frame,
            text=self._truncate_message(self.message),
            font=(FONTS['system'][0], FONTS['body_medium']),
            fg=APPLE_COLORS['text_primary'],
            bg=APPLE_COLORS['surface'],
            wraplength=300,
            justify='left'
        )
        self.message_label.pack(anchor='w')
        
        # Full message (hidden by default)
        if self.notification_type == 'error':
            self.full_message = tk.Text(
                message_frame,
                height=4,
                width=40,
                font=(FONTS['system'][0], FONTS['body_small']),
                fg=APPLE_COLORS['text_primary'],
                bg=APPLE_COLORS['surface'],
                bd=0,
                wrap='word'
            )
            self.full_message.insert('1.0', self.message)
            self.full_message.config(state='disabled')
            # Hide initially
            self.full_message.pack_forget()
    
    def _truncate_message(self, message, max_length=50):
        """Truncate message for compact display"""
        if len(message) > max_length:
            return message[:max_length] + "..."
        return message
    
    def _on_click(self, event):
        """Handle click event"""
        self.is_paused = True
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded and hasattr(self, 'full_message'):
            # Show full message
            self.message_label.pack_forget()
            self.full_message.pack(anchor='w', fill='both', expand=True)
            self.full_message.config(state='normal')
        elif hasattr(self, 'full_message'):
            # Show truncated message
            self.full_message.pack_forget()
            self.message_label.pack(anchor='w')
        
        # Update window size
        self.update_idletasks()
        self._position_window()
    
    def _on_enter(self, event):
        """Pause on mouse enter"""
        self.is_paused = True
    
    def _on_leave(self, event):
        """Resume on mouse leave"""
        self.is_paused = False
        # Start dismiss timer
        self.after(500, self._check_dismiss)
    
    def _check_dismiss(self):
        """Check if should dismiss"""
        if not self.is_paused and self.animation_direction == 1:
            self._start_slide_out()
    
    def _position_window(self):
        """Position notification window"""
        self.update_idletasks()
        
        # Get window size
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        
        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        
        # Position at top-right of parent
        x = parent_x + parent_width - width - 20
        y = parent_y + 80  # Below title bar
        
        # Set initial position (off-screen for animation)
        self.start_x = x + width + 20
        self.end_x = x
        self.current_y = y
        
        self.geometry(f"{width}x{height}+{self.start_x}+{y}")
    
    def _animate(self):
        """Animate notification slide in/out"""
        if self.animation_direction == 1:
            # Slide in
            self.animation_progress += 1.0 / (ANIMATION_FPS * ANIMATION_DURATION / 1000)
            if self.animation_progress >= 1.0:
                self.animation_progress = 1.0
                # Schedule slide out after duration
                self.after(self.duration, self._start_slide_out)
        else:
            # Slide out
            self.animation_progress -= 1.0 / (ANIMATION_FPS * ANIMATION_DURATION / 1000)
            if self.animation_progress <= 0.0:
                self.destroy()
                return
        
        # Calculate position with easing
        progress = self._ease_out_cubic(self.animation_progress)
        current_x = int(self.start_x + (self.end_x - self.start_x) * progress)
        
        # Update position
        self.geometry(f"+{current_x}+{self.current_y}")
        
        # Continue animation
        self.after(1000 // ANIMATION_FPS, self._animate)
    
    def _start_slide_out(self):
        """Start slide out animation"""
        if not self.is_paused:
            self.animation_direction = -1
    
    def _ease_out_cubic(self, t):
        """Easing function for smooth animation"""
        return 1 - pow(1 - t, 3)
    
    def update_position(self, y_offset):
        """Update Y position for stacking"""
        self.current_y = y_offset
        self.geometry(f"+{self.winfo_x()}+{y_offset}")

class NotificationManager:
    """Manages notification queue and display"""
    
    def __init__(self, parent):
        self.parent = parent
        self.queue = Queue()
        self.active_notifications = []
        self.max_notifications = 3
        self.enable_animations = True
        self.notification_spacing = 10
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
    
    def show_notification(self, message, notification_type="info", duration=NOTIFICATION_DURATION):
        """Add notification to queue"""
        self.queue.put((message, notification_type, duration))
    
    def _process_queue(self):
        """Process notification queue"""
        while True:
            try:
                # Get notification from queue
                message, notification_type, duration = self.queue.get(timeout=0.1)
                
                # Wait if too many notifications
                while len(self.active_notifications) >= self.max_notifications:
                    # Remove destroyed notifications
                    self.active_notifications = [
                        n for n in self.active_notifications 
                        if n.winfo_exists()
                    ]
                    time.sleep(0.1)
                
                # Create notification in main thread
                self.parent.after(0, lambda: self._create_notification(
                    message, notification_type, duration
                ))
                
            except:
                # Queue is empty, continue
                pass
    
    def _create_notification(self, message, notification_type, duration):
        """Create and show notification"""
        if self.enable_animations:
            notification = NotificationWidget(
                self.parent, message, notification_type, duration
            )
            self.active_notifications.append(notification)
            
            # Adjust positions of existing notifications
            self._reposition_notifications()
        else:
            # Simple message box for no animations
            print(f"[{notification_type.upper()}] {message}")
    
    def _reposition_notifications(self):
        """Reposition all active notifications with proper spacing"""
        y_offset = 80
        for notification in self.active_notifications:
            if notification.winfo_exists():
                notification.update_position(y_offset)
                y_offset += notification.winfo_reqheight() + self.notification_spacing