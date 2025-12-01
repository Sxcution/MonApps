import os
import json
import glob

def cleanup_images(autokey_root):
    """
    Delete images in 'captures' folder that are NOT referenced by any saved macro in 'Save' folder.
    """
    save_dir = os.path.join(autokey_root, "Save")
    captures_dir = os.path.join(autokey_root, "captures")
    
    if not os.path.exists(save_dir) or not os.path.exists(captures_dir):
        print("⚠️ Save or Captures directory not found, skipping cleanup.")
        return

    # 1. Collect all used image paths from saved JSON files
    used_images = set()
    json_files = glob.glob(os.path.join(save_dir, "*.json"))
    
    print(f"🧹 Cleanup: Scanning {len(json_files)} macro files...")
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle both list of events (new format) and dict wrapper (old format)
            events = data if isinstance(data, list) else data.get('events', [])
            
            for event in events:
                # Check for 'detect_image' or 'auto_detect' events
                if event.get('type') == 'detect_image':
                    img_path = event.get('image_path')
                    if img_path:
                        used_images.add(os.path.abspath(img_path).lower())
                        
                elif event.get('type') == 'auto_detect':
                    # auto_detect has a list of image paths
                    for img_info in event.get('image_detects', []):
                        img_path = img_info.get('path')
                        if img_path:
                            used_images.add(os.path.abspath(img_path).lower())
                            
        except Exception as e:
            print(f"⚠️ Error reading {filepath}: {e}")

    print(f"🧹 Cleanup: Found {len(used_images)} used images.")

    # 2. Scan captures folder and delete unused images
    deleted_count = 0
    capture_files = glob.glob(os.path.join(captures_dir, "*"))
    
    for file_path in capture_files:
        # Only check files, not directories
        if not os.path.isfile(file_path):
            continue
            
        # Check if it's an image (simple extension check)
        if not file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            continue
            
        abs_path = os.path.abspath(file_path).lower()
        
        if abs_path not in used_images:
            try:
                os.remove(file_path)
                print(f"🗑️ Deleted unused image: {os.path.basename(file_path)}")
                deleted_count += 1
            except Exception as e:
                print(f"⚠️ Failed to delete {file_path}: {e}")

    if deleted_count > 0:
        print(f"✨ Cleanup complete: Deleted {deleted_count} unused images.")
    else:
        print("✨ Cleanup complete: No unused images found.")
