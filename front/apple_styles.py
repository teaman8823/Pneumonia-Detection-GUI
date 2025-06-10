# front/apple_styles.py

import tkinter as tk
from tkinter import ttk
from front.config import APPLE_COLORS, FONTS, PADDING, CORNER_RADIUS

class AppleStyleManager:
    """Manages Apple-style theming for ttk widgets"""
    
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style(root)
        self._font_cache = {}
        
    def get_font(self, size, weight='normal'):
        """Get or create font with caching"""
        key = (size, weight)
        if key not in self._font_cache:
            font_families = FONTS['system']
            for family in font_families:
                try:
                    self._font_cache[key] = (family, size, weight)
                    # Test if font exists
                    tk.font.Font(family=family, size=size, weight=weight)
                    break
                except Exception:
                    continue
            else:
                # Fallback to default
                self._font_cache[key] = ('Helvetica', size, weight)
        return self._font_cache[key]
    
    def apply_apple_styles(self):
        """Apply Apple-style configurations to all ttk widgets"""
        
        # Configure root window
        self.root.configure(bg=APPLE_COLORS['surface'])
        
        # Main frame style - transparent background
        self.style.configure('AppleMain.TFrame',
            background=APPLE_COLORS['surface'],
            relief='flat',
            borderwidth=0
        )
        
        # Card frame style (white background with shadow effect)
        self.style.configure('AppleCard.TFrame',
            background=APPLE_COLORS['surface'],
            relief='flat',
            borderwidth=1,
            lightcolor=APPLE_COLORS['separator'],
            darkcolor=APPLE_COLORS['separator']
        )
        
        # Primary button style - Changed to normal button style
        self.style.configure('ApplePrimary.TButton',
            font=self.get_font(FONTS['body_medium']),
            foreground=APPLE_COLORS['text_primary'],
            background=APPLE_COLORS['surface'],
            focuscolor='none',
            borderwidth=1,
            relief='flat',
            padding=(PADDING['large'], PADDING['small'])
        )
        
        # Primary button map - Normal button behavior
        self.style.map('ApplePrimary.TButton',
            background=[
                ('disabled', APPLE_COLORS['separator']),
                ('pressed', APPLE_COLORS['separator']),
                ('active', APPLE_COLORS['background'])
            ],
            foreground=[
                ('disabled', APPLE_COLORS['text_tertiary'])
            ]
        )
        
        # Secondary button style
        self.style.configure('AppleSecondary.TButton',
            font=self.get_font(FONTS['body_medium']),
            foreground=APPLE_COLORS['text_primary'],
            background=APPLE_COLORS['surface'],
            focuscolor='none',
            borderwidth=1,
            relief='flat',
            padding=(PADDING['large'], PADDING['small'])
        )
        
        self.style.map('AppleSecondary.TButton',
            background=[
                ('pressed', APPLE_COLORS['separator']),
                ('active', APPLE_COLORS['background'])
            ]
        )
        
        # Label styles with transparent background
        self.style.configure('AppleTitle.TLabel',
            font=self.get_font(FONTS['title_large'], 'bold'),
            foreground=APPLE_COLORS['text_primary'],
            background=APPLE_COLORS['surface']
        )
        
        self.style.configure('AppleBody.TLabel',
            font=self.get_font(FONTS['body_medium']),
            foreground=APPLE_COLORS['text_primary'],
            background=APPLE_COLORS['surface']
        )
        
        self.style.configure('AppleSecondary.TLabel',
            font=self.get_font(FONTS['body_small']),
            foreground=APPLE_COLORS['text_secondary'],
            background=APPLE_COLORS['surface']
        )
        
        # New metric styles with transparent background
        self.style.configure('AppleMetrics.TLabel',
            font=self.get_font(FONTS['caption']),
            foreground=APPLE_COLORS['text_secondary'],
            background=APPLE_COLORS['surface']
        )
        
        self.style.configure('AppleValue.TLabel',
            font=self.get_font(20, 'bold'),
            foreground=APPLE_COLORS['text_primary'],
            background=APPLE_COLORS['surface']
        )
        
        # Entry style
        self.style.configure('Apple.TEntry',
            font=self.get_font(FONTS['body_medium']),
            foreground=APPLE_COLORS['text_primary'],
            fieldbackground=APPLE_COLORS['surface'],
            borderwidth=1,
            relief='flat',
            insertcolor=APPLE_COLORS['primary']
        )
        
        self.style.map('Apple.TEntry',
            fieldbackground=[
                ('focus', APPLE_COLORS['surface'])
            ],
            bordercolor=[
                ('focus', APPLE_COLORS['primary'])
            ]
        )
        
        # Combobox style
        self.style.configure('Apple.TCombobox',
            font=self.get_font(FONTS['body_medium']),
            foreground=APPLE_COLORS['text_primary'],
            fieldbackground=APPLE_COLORS['surface'],
            background=APPLE_COLORS['surface'],
            borderwidth=1,
            relief='flat',
            arrowcolor=APPLE_COLORS['text_secondary']
        )
        
        # Notebook (tabs) style with equal width
        self.style.configure('Apple.TNotebook',
            background=APPLE_COLORS['surface'],
            borderwidth=0,
            relief='flat',
            tabmargins=[0, 0, 0, 0]
        )
        
        self.style.configure('Apple.TNotebook.Tab',
            font=self.get_font(FONTS['body_medium']),
            foreground=APPLE_COLORS['text_secondary'],
            background=APPLE_COLORS['surface'],
            padding=[PADDING['xlarge'], PADDING['medium']],
            borderwidth=0,
            focuscolor='none'
        )
        
        self.style.map('Apple.TNotebook.Tab',
            foreground=[
                ('selected', APPLE_COLORS['primary'])
            ],
            background=[
                ('selected', APPLE_COLORS['surface'])
            ]
        )
        
        # Progressbar style
        self.style.configure('Apple.Horizontal.TProgressbar',
            background=APPLE_COLORS['primary'],
            troughcolor=APPLE_COLORS['separator'],
            borderwidth=0,
            relief='flat',
            darkcolor=APPLE_COLORS['primary'],
            lightcolor=APPLE_COLORS['primary']
        )
        
        # Treeview style with centered text and proper row height
        self.style.configure('Apple.Treeview',
            font=self.get_font(FONTS['body_small']),
            foreground=APPLE_COLORS['text_primary'],
            background=APPLE_COLORS['surface'],
            fieldbackground=APPLE_COLORS['surface'],
            borderwidth=0,
            relief='flat',
            rowheight=80  # Increased for multi-line content
        )
        
        self.style.configure('Apple.Treeview.Heading',
            font=self.get_font(FONTS['body_small'], 'bold'),
            foreground=APPLE_COLORS['text_secondary'],
            background=APPLE_COLORS['surface'],
            relief='flat',
            borderwidth=0
        )
        
        self.style.map('Apple.Treeview',
            background=[
                ('selected', APPLE_COLORS['primary'])
            ],
            foreground=[
                ('selected', 'white')
            ]
        )
        
        # Scrollbar style
        self.style.configure('Apple.Vertical.TScrollbar',
            background=APPLE_COLORS['background'],
            bordercolor=APPLE_COLORS['background'],
            arrowcolor=APPLE_COLORS['text_tertiary'],
            troughcolor=APPLE_COLORS['background'],
            darkcolor=APPLE_COLORS['text_tertiary'],
            lightcolor=APPLE_COLORS['text_tertiary'],
            borderwidth=0,
            relief='flat',
            width=14
        )
        
        self.style.configure('Apple.Horizontal.TScrollbar',
            background=APPLE_COLORS['background'],
            bordercolor=APPLE_COLORS['background'],
            arrowcolor=APPLE_COLORS['text_tertiary'],
            troughcolor=APPLE_COLORS['background'],
            darkcolor=APPLE_COLORS['text_tertiary'],
            lightcolor=APPLE_COLORS['text_tertiary'],
            borderwidth=0,
            relief='flat',
            width=14
        )