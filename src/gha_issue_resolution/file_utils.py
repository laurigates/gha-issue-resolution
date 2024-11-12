from pathlib import Path
import traceback

def get_repo_structure():
    """Get a string representation of the repository structure"""
    structure = ""
    try:
        # Define directories to ignore
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.pytest_cache', '.venv', 'venv', 'dist', 'build'}
        
        # Define extensions to include
        valid_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.yml', '.yaml', '.json', '.md', '.txt'}
        
        for file in Path('.').rglob('*'):
            # Skip ignored directories and their contents
            if any(ignore_dir in file.parts for ignore_dir in ignore_dirs):
                continue
                
            # Only include files with valid extensions
            if file.is_file() and file.suffix in valid_extensions:
                relative_path = file.relative_to('.')
                structure += f"- {relative_path}\n"
                
        print(f"Found {len(structure.splitlines())} relevant files")
        return structure
    except Exception as e:
        print(f"Error getting repository structure: {str(e)}")
        print(traceback.format_exc())
        return "Error getting repository structure"

def get_file_content(file_path, max_chars=100000):
    """Get the content of a file with optional size limit"""
    try:
        path = Path(file_path)
        
        # Additional safety checks
        if not path.is_file():
            return f"Error: {file_path} is not a file"
            
        if path.suffix not in {'.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.yml', '.yaml', '.json', '.md', '.txt'}:
            return f"Error: {file_path} has unsupported file type"
            
        # Check file size before reading
        if path.stat().st_size > max_chars:
            print(f"Warning: {file_path} exceeds size limit of {max_chars} chars")
            
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read(max_chars)
            if len(content) == max_chars:
                content += "\n... (file truncated due to size)"
            return content
    except UnicodeDecodeError:
        print(f"Warning: Could not read {file_path} as text, skipping")
        return f"Error: Could not read {file_path} - not a text file"
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        print(traceback.format_exc())
        return f"Error reading file: {str(e)}"