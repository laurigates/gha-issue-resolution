"""Module for analyzing repository files"""

from pathlib import Path
from typing import List, Set
from gha_issue_resolution.file_utils import get_repo_structure, get_file_content

def get_relevant_files(repo_structure: str) -> List[str]:
    """Get files that are likely relevant to code changes"""
    relevant_extensions: Set[str] = {
        '.py', '.js', '.ts', '.jsx', '.tsx', 
        '.html', '.css', '.yml', '.yaml', 
        '.json', '.md', '.txt'
    }
    
    files = []
    for line in repo_structure.split('\n'):
        if line.strip():
            file_path = line.strip('- ').strip()
            if any(file_path.endswith(ext) for ext in relevant_extensions):
                files.append(file_path)
    
    return files

def prepare_file_contents(files: List[str]) -> List[tuple[str, str]]:
    """Prepare contents of relevant files for analysis"""
    file_contents = []
    
    for file_path in files:
        if Path(file_path).is_file():
            content = get_file_content(file_path)
            if content.strip():
                file_contents.append((file_path, content))
                
    return file_contents
