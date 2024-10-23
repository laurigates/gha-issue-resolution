from pathlib import Path
import traceback

def get_repo_structure():
    structure = ""
    for file in Path('.').rglob('*'):
        if file.is_file() and '.git' not in file.parts:
            structure += f"- {file}\n"
    return structure

def get_file_content(file_path, max_chars=100000):
    try:
        with open(file_path, 'r') as file:
            content = file.read(max_chars)
            if len(content) == max_chars:
                content += "\n... (file truncated due to size)"
            return content
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        print(traceback.format_exc())
        return f"Error reading file: {str(e)}"
