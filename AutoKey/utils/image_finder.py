"""
Image finding utilities using OpenCV
"""
import cv2
import numpy as np
from mss import mss


def find_image_on_screen(template_path, confidence=0.8, region=None):
    """
    Find template image on screen
    
    Args:
        template_path: Path to template image file
        confidence: Match confidence (0.0 to 1.0)
        region: Optional dict with 'left', 'top', 'width', 'height' to restrict search area
    
    Returns:
        (x, y, width, height) if found, None otherwise
    """
    try:
        # Load template
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"Failed to load template: {template_path}")
            return None
        
        # Capture screen
        with mss() as sct:
            if region:
                monitor = region
            else:
                monitor = sct.monitors[1]  # Primary monitor
            
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # Template matching
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= confidence:
            h, w = template.shape[:2]
            x, y = max_loc
            
            # Adjust coordinates if region was specified
            if region:
                x += region.get('left', 0)
                y += region.get('top', 0)
            
            return (x, y, w, h)
        
        return None
        
    except Exception as e:
        print(f"Error finding image: {e}")
        return None


def wait_for_image(template_path, timeout=30, confidence=0.8, region=None, check_interval=0.5):
    """
    Wait for image to appear on screen
    
    Args:
        template_path: Path to template image
        timeout: Maximum seconds to wait
        confidence: Match confidence
        region: Optional search region
        check_interval: Seconds between checks
    
    Returns:
        (x, y, width, height) if found within timeout, None otherwise
    """
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = find_image_on_screen(template_path, confidence, region)
        if result:
            return result
        time.sleep(check_interval)
    
    return None
