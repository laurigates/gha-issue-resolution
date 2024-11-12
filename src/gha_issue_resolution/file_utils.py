"""Utility functions for file operations in GitHub Actions environment"""
from pathlib import Path
import os
import traceback

def get_repo_root():
    """Get the root directory of the target repository"""
    # In GitHub Actions, GITHUB_WORKSPACE points to the checked out repository
    workspace = os.environ.get('GITHUB_WORKSPACE')
    if workspace:
        return Path(workspace)
    # Fallback to current directory if not in GitHub Actions
    return Path('.')

def get_repo_structure():
    """Get a string representation of the repository structure"""
    repo_root = get_repo_root()
    structure = []
    try:
        print(f"\nScanning repository at: {repo_root}")
        for file in sorted(repo_root.rglob('*')):
            if file.is_file() and '.git' not in file.parts:
                # Get path relative to repo root
                rel_path = file.relative_to(repo_root)
                structure.append(f"- {rel_path}")
                print(f"Found: {rel_path}")
        
        if not structure:
            print("Warning: No files found in repository")
            
        return '\n'.join(structure)
    except Exception as e:
        print(f"Error getting repository structure: {str(e)}")
        print(traceback.format_exc())
        return "Error getting repository structure"

def get_file_content(file_path, max_chars=100000):
    """Get the content of a file with optional size limit"""
    repo_root = get_repo_root()
    full_path = repo_root / file_path
    
    try:
        print(f"Reading file: {full_path}")
        with open(full_path, 'r', encoding='utf-8') as file:
            content = file.read(max_chars)
            if len(content) == max_chars:
                content += "\n... (file truncated due to size)"
            print(f"Successfully read {len(content)} characters")
            return content
    except UnicodeDecodeError:
        print(f"Warning: Could not read {file_path} as text, skipping")
        return f"Error: Could not read {file_path} - not a text file"
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        print(traceback.format_exc())
        return f"Error reading file: {str(e)}"

def is_relevant_file(file_path):
    """Check if a file is relevant for analysis"""
    relevant_extensions = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css',
        '.yml', '.yaml', '.json', '.md', '.txt'
    }
    return any(str(file_path).endswith(ext) for ext in relevant_extensions)

def get_relevant_files():
    """Get list of repository files relevant for analysis"""
    repo_root = get_repo_root()
    files = []
    
    print(f"\nScanning for relevant files in: {repo_root}")
    try:
        for file in sorted(repo_root.rglob('*')):
            if file.is_file() and '.git' not in file.parts:
                rel_path = file.relative_to(repo_root)
                if is_relevant_file(rel_path):
                    files.append(str(rel_path))
                    print(f"Added: {rel_path}")
    except Exception as e:
        print(f"Error scanning repository: {str(e)}")
        print(traceback.format_exc())
    
    print(f"\nFound {len(files)} relevant files")
    return files