import cv2
import numpy as np
import mss
import time
from typing import Optional, Tuple

def wait_for_image(template_path: str,
                   region: Optional[Tuple[int,int,int,int]] = None,  # (x1,y1,x2,y2)
                   timeout_ms: int = 60000,
                   poll_interval_ms: int = 150,
                   threshold: float = 0.85) -> Optional[Tuple[int,int]]:
    """
    Repeatedly capture the screen (or region) with mss and run
    cv2.matchTemplate(cv2.TM_CCOEFF_NORMED). Return the center (x,y)
    of the best match when max_val >= threshold. Return None on timeout.
    """
    
    # Load template
    template = cv2.imread(template_path)
    if template is None:
        print(f"Error: Could not load template image: {template_path}")
        return None
        
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    h, w = template_gray.shape[:2]
    
    start_time = time.time()
    
    with mss.mss() as sct:
        while (time.time() - start_time) * 1000 < timeout_ms:
            try:
                # Define capture region
                if region:
                    monitor = {"top": region[1], "left": region[0], "width": region[2]-region[0], "height": region[3]-region[1]}
                else:
                    monitor = sct.monitors[1] # Primary monitor
                
                # Capture screen
                sct_img = sct.grab(monitor)
                img = np.array(sct_img)
                img_gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                
                # Match template
                result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= threshold:
                    # Calculate center
                    # max_loc is top-left of match in the captured image
                    match_x = max_loc[0]
                    match_y = max_loc[1]
                    
                    # Adjust for region offset if applicable
                    offset_x = monitor["left"]
                    offset_y = monitor["top"]
                    
                    center_x = offset_x + match_x + w // 2
                    center_y = offset_y + match_y + h // 2
                    
                    return (center_x, center_y)
                    
            except Exception as e:
                print(f"Error in wait_for_image: {e}")
                
            time.sleep(poll_interval_ms / 1000.0)
            
    return None
