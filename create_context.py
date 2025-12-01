import os

# Configuration
ALLOWED_EXTENSIONS = {
    '.py', '.pyw', '.html', '.css', '.js', '.json', 
    '.md', '.ahk', '.xml', '.yaml', '.yml', '.ini', '.txt', '.bat', '.sh'
}

IGNORED_DIRS = {
    '.git', '.venv', '__pycache__', 'node_modules', 'dist', 'build', 
    'bin', 'obj', '.idea', '.vscode', 'captured_images', 'Rebuilt', 
    'java', 'venv', 'env', '.cursor', 'img', 'images', 'videos'
}

IGNORED_FILES = {
    'package-lock.json', 'yarn.lock', 'poetry.lock', 'Project_Context.txt', 'create_context.py'
}

MAX_FILE_SIZE_MB = 1.0  # Skip individual text files larger than 1MB
OUTPUT_FILE = 'Project_Context.txt'

def is_text_file(filename):
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

def create_context_file(root_dir):
    total_files = 0
    total_size = 0
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# Project Context Export\n")
        outfile.write(f"# Root: {root_dir}\n")
        outfile.write(f"# Generated on: {os.popen('date /t').read().strip()}\n\n")
        
        for root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            
            for file in files:
                if file in IGNORED_FILES:
                    continue
                    
                if not is_text_file(file):
                    continue
                
                file_path = os.path.join(root, file)
                
                # Skip if file is too large
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                        print(f"Skipping large file: {file_path} ({file_size/1024/1024:.2f} MB)")
                        continue
                except OSError:
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()
                        
                        # Write header
                        rel_path = os.path.relpath(file_path, root_dir)
                        outfile.write(f"\n{'='*50}\n")
                        outfile.write(f"FILE: {rel_path}\n")
                        outfile.write(f"{'='*50}\n")
                        outfile.write(content)
                        outfile.write("\n")
                        
                        total_files += 1
                        total_size += len(content.encode('utf-8'))
                        
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    print(f"\nSuccess! Created {OUTPUT_FILE}")
    print(f"Total files included: {total_files}")
    print(f"Total size: {total_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    create_context_file(os.getcwd())
