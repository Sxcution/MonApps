import cv2
import numpy as np
import pyautogui
import time
import os

class ImageFinder:
    @staticmethod
    def find_image_on_screen(template_path, confidence=0.8, timeout=30):
        """
        Waits for an image to appear on screen.
        Returns (x, y) center coordinates if found, else None.
        """
        if not os.path.exists(template_path):
            print(f"Template not found: {template_path}")
            return None

        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            try:
                # Take screenshot
                screenshot = pyautogui.screenshot()
                screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # Load template
                template = cv2.imread(template_path)
                
                # Match template
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= confidence:
                    # Calculate center
                    h, w = template.shape[:2]
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    return (center_x, center_y)
                    
            except Exception as e:
                print(f"Error finding image: {e}")
                
            time.sleep(0.5)
            
        return None
