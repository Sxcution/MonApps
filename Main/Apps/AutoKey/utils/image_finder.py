"""
Image finding utilities using OpenCV
"""
import cv2
import numpy as np
from mss import mss


def find_image_on_screen(template_path, confidence=0.8, region=None, grayscale=False, multi_scale=False):
    """
    Find template image on screen with advanced options.
    
    Args:
        template_path: Path to template image file
        confidence: Match confidence (0.0 to 1.0)
        region: Optional dict with 'left', 'top', 'width', 'height'
        grayscale: Boolean, convert to grayscale before matching
        multi_scale: Boolean, search at multiple scales (0.8 to 1.2)
    
    Returns:
        (x, y, width, height) if found, None otherwise
    """
    try:
        # Load template
        # IMREAD_UNCHANGED needed to keep Alpha channel for masking
        template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
        if template is None:
            print(f"Failed to load template: {template_path}")
            return None
            
        # Handle Template Transparency (Mask)
        mask = None
        if template.shape[2] == 4:
            # Extract Alpha channel as mask
            channels = cv2.split(template)
            mask = channels[3]
            # Remove alpha from template for matching
            template = cv2.merge(channels[:3])
        
        # Capture screen
        with mss() as sct:
            if region:
                monitor = region
            else:
                monitor = sct.monitors[1]  # Primary monitor
            
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
        # Grayscale Conversion
        if grayscale:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            # Mask is already single channel, no need to convert
            
        # Multi-scale Search
        scales = [1.0]
        if multi_scale:
            # Search from 60% to 160% size (broader range)
            scales = np.linspace(0.6, 1.6, 11) 
            
        found = None
        max_val_found = -1
        
        for scale in scales:
            # Resize template (or image) - resizing template is usually faster if image is big
            
            if scale != 1.0:
                width = int(template.shape[1] * scale)
                height = int(template.shape[0] * scale)
                
                # Skip if too small (noise)
                if width < 8 or height < 8:
                    continue
                    
                resized_template = cv2.resize(template, (width, height))
                # Use INTER_NEAREST for mask to avoid gray edges
                resized_mask = cv2.resize(mask, (width, height), interpolation=cv2.INTER_NEAREST) if mask is not None else None
            else:
                resized_template = template
                resized_mask = mask
                
            # Skip if template is larger than image
            if resized_template.shape[0] > img.shape[0] or resized_template.shape[1] > img.shape[1]:
                continue
                
            # Template matching
            # TM_CCORR_NORMED works better with mask in OpenCV
            if resized_mask is not None:
                method = cv2.TM_CCORR_NORMED
                result = cv2.matchTemplate(img, resized_template, method, mask=resized_mask)
            else:
                method = cv2.TM_CCOEFF_NORMED
                result = cv2.matchTemplate(img, resized_template, method)
                
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > max_val_found:
                max_val_found = max_val
                found = (max_loc, resized_template.shape)
                
        if max_val_found >= confidence and found:
            max_loc, shape = found
            h, w = shape[:2]
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


def wait_for_image(template_path, timeout=30, confidence=0.8, region=None, check_interval=0.5, grayscale=False, multi_scale=False):
    """
    Wait for image to appear on screen
    
    Args:
        template_path: Path to template image
        timeout: Maximum seconds to wait
        confidence: Match confidence
        region: Optional search region
        check_interval: Seconds between checks
        grayscale: Boolean
        multi_scale: Boolean
    
    Returns:
        (x, y, width, height) if found within timeout, None otherwise
    """
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = find_image_on_screen(template_path, confidence, region, grayscale, multi_scale)
        if result:
            return result
        time.sleep(check_interval)
    
    return None
