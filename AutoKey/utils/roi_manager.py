"""
ROI Manager - Screen/Window/Custom region capture
Supports rate limiting and multiple capture backends
"""
import mss
import numpy as np
import time
from typing import Tuple, Optional
import win32gui
import win32ui
import win32con
from dataclasses import dataclass

@dataclass
class Region:
    """Screen region definition"""
    x: int
    y: int
    width: int
    height: int
    
    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Return as (x1, y1, x2, y2)"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    @property
    def mss_monitor(self) -> dict:
        """Return as mss monitor dict"""
        return {
            'left': self.x,
            'top': self.y,
            'width': self.width,
            'height': self.height
        }

class ROIManager:
    """Manage screen region capture with rate limiting"""
    
    def __init__(self, rate_limit_fps=10):
        """
        Initialize ROI Manager
        Args:
            rate_limit_fps: Maximum capture rate (fps)
        """
        self.sct = mss.mss()
        self.rate_limit_fps = rate_limit_fps
        self.min_interval = 1.0 / rate_limit_fps if rate_limit_fps > 0 else 0
        self.last_capture_time = 0
    
    def get_screen_region(self) -> Region:
        """Get full screen region"""
        monitor = self.sct.monitors[1]  # Primary monitor
        return Region(
            x=monitor['left'],
            y=monitor['top'],
            width=monitor['width'],
            height=monitor['height']
        )
    
    def get_window_region(self, window_title: Optional[str] = None) -> Optional[Region]:
        """
        Get active/specified window region
        Args:
            window_title: Window title to find (None = active window)
        Returns:
            Region or None if window not found
        """
        try:
            if window_title:
                # Find window by title
                hwnd = win32gui.FindWindow(None, window_title)
            else:
                # Get foreground window
                hwnd = win32gui.GetForegroundWindow()
            
            if hwnd == 0:
                return None
            
            # Get window rect
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x2, y2 = rect
            
            return Region(
                x=x,
                y=y,
                width=x2 - x,
                height=y2 - y
            )
        except Exception as e:
            print(f"⚠️ ROI: Failed to get window region: {e}")
            return None
    
    def capture(self, region=None) -> Optional[np.ndarray]:
        """
        Capture screenshot with rate limiting
        Args:
            region: Region to capture (dict or Region object, None = full screen)
        Returns:
            BGR image as numpy array or None if rate limited
        """
        # Rate limiting
        now = time.time()
        elapsed = now - self.last_capture_time
        if elapsed < self.min_interval:
            return None  # Skip this capture
        
        self.last_capture_time = now
        
        # Determine monitor dict
        if region is None:
            # Full screen
            monitor = self.sct.monitors[1]
        elif isinstance(region, dict):
            # Already a dict with left/top/width/height
            monitor = region
        else:
            # Region object
            monitor = {
                'left': region.x,
                'top': region.y,
                'width': region.width,
                'height': region.height
            }
        
        # Capture
        try:
            screenshot = self.sct.grab(monitor)
            # Convert to numpy array (BGRA -> BGR)
            img = np.array(screenshot)
            img = img[:, :, :3]  # Drop alpha channel
            img = img[:, :, ::-1]  # RGB -> BGR
            return img
        except Exception as e:
            print(f"⚠️ ROI: Capture failed: {e}")
            return None
    
    def capture_with_retry(self, region: Optional[Region] = None, max_retries=3) -> Optional[np.ndarray]:
        """
        Capture with retry logic (ignores rate limit for retries)
        Args:
            region: Region to capture
            max_retries: Maximum retry attempts
        Returns:
            BGR image or None
        """
        for attempt in range(max_retries):
            # Temporarily disable rate limit for retries
            old_interval = self.min_interval
            if attempt > 0:
                self.min_interval = 0
            
            img = self.capture(region)
            
            # Restore rate limit
            self.min_interval = old_interval
            
            if img is not None:
                return img
            
            time.sleep(0.05)  # Short delay before retry
        
        return None
