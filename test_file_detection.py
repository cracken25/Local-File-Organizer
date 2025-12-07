import os

def collect_file_paths(base_path):
    """Collect all file paths from the base directory or single file, excluding hidden files."""
    print(f"Scanning: {base_path}")
    if os.path.isfile(base_path):
        return [base_path]
    else:
        file_paths = []
        for root, _, files in os.walk(base_path):
            print(f"Root: {root}")
            print(f"Files found: {files}")
            for file in files:
                if not file.startswith('.'):  # Exclude hidden files
                    file_paths.append(os.path.join(root, file))
        return file_paths

# Path from user logs
test_path = "/Users/jeffmccracken/Library/CloudStorage/GoogleDrive-jeff.mccracken@gmail.com/My Drive/TestFileInputFolder"

if os.path.exists(test_path):
    print(f"Path exists: {test_path}")
    files = collect_file_paths(test_path)
    print(f"Total files found: {len(files)}")
    for f in files:
        print(f" - {f}")
else:
    print(f"Path does not exist: {test_path}")
    # List parent directory to see what's there
    parent = os.path.dirname(test_path)
    if os.path.exists(parent):
        print(f"Parent exists: {parent}")
        print(os.listdir(parent))
    else:
        print(f"Parent does not exist: {parent}")
