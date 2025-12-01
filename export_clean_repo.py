import os
import shutil

# Configuration
SOURCE_DIR = os.getcwd()
DEST_DIR = os.path.join(os.path.dirname(SOURCE_DIR), "Mon_Lite")

ALLOWED_EXTENSIONS = {
    '.py', '.pyw', '.html', '.css', '.js', '.json', 
    '.md', '.ahk', '.xml', '.yaml', '.yml', '.ini', '.txt', '.bat', '.sh'
}

IGNORED_DIRS = {
    '.git', '.venv', '__pycache__', 'node_modules', 'dist', 'build', 
    'bin', 'obj', '.idea', '.vscode', 'captured_images', 'Rebuilt', 
    'java', 'venv', 'env', '.cursor', 'img', 'images', 'videos',
    'Mon_Lite' # Avoid recursive copy if inside
}

MAX_FILE_SIZE_MB = 2.0  # Skip individual files larger than 2MB

def is_source_file(filename):
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

def export_clean_repo():
    if os.path.exists(DEST_DIR):
        print(f"Removing existing {DEST_DIR}...")
        shutil.rmtree(DEST_DIR)
    
    print(f"Copying clean source code to {DEST_DIR}...")
    
    copied_count = 0
    total_size = 0
    
    for root, dirs, files in os.walk(SOURCE_DIR):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        
        # Calculate relative path to maintain structure
        rel_path = os.path.relpath(root, SOURCE_DIR)
        dest_root = os.path.join(DEST_DIR, rel_path)
        
        if not os.path.exists(dest_root):
            os.makedirs(dest_root)
            
        for file in files:
            if not is_source_file(file):
                continue
                
            src_file = os.path.join(root, file)
            
            # Skip large files
            try:
                file_size = os.path.getsize(src_file)
                if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    continue
            except OSError:
                continue
                
            dest_file = os.path.join(dest_root, file)
            
            try:
                shutil.copy2(src_file, dest_file)
                copied_count += 1
                total_size += file_size
            except Exception as e:
                print(f"Failed to copy {src_file}: {e}")

    print(f"\nSuccess! Exported to: {DEST_DIR}")
    print(f"Total files: {copied_count}")
    print(f"Total size: {total_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    export_clean_repo()
