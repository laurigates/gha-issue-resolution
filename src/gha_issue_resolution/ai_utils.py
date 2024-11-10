import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai.types import GenerationConfig
import traceback
import re
from pathlib import Path
from gha_issue_resolution.file_utils import get_file_content

# Setup Gemini API constants
MODEL_ID = 'gemini-1.5-flash-002'
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '8192'))

# Set model parameters
generation_config = GenerationConfig(
    temperature=0.7,
    top_p=1.0,
    top_k=32,
    candidate_count=1,
    max_output_tokens=MAX_TOKENS,
)

# Set safety settings
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

def setup_ai():
    """Initialize the Gemini API"""
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])

def query_gemini(prompt):
    try:
        model = genai.GenerativeModel(
            MODEL_ID,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
        response = model.generate_content([
            genai.types.ContentDict({
                'role': 'user',
                'parts': [
                    """You are an AI assistant specialized in analyzing GitHub issues and suggesting solutions.
                    When suggesting code changes, you MUST follow these rules EXACTLY:

                    1. First, analyze the issue and explain what needs to be changed
                    2. For EACH file that needs modification, you MUST use this exact format:

                    File: path/to/file.py (CURRENT CONTENT)
                    ```python
                    # Show the current content of the file
                    ```

                    Changes to make:
                    - List the specific changes needed

                    File: path/to/file.py (WITH CHANGES)
                    ```python
                    # Show the complete new content with your changes
                    ```

                    3. The file paths must be exact and match the repository structure
                    4. Every changed file must have both (CURRENT CONTENT) and (WITH CHANGES) blocks
                    5. Include complete file contents in both blocks, not just the changed portions
                    """,
                    prompt
                ]
            })
        ])
        print(f"\nUsage metadata:\n{response.prompt_feedback}")
        print(f"\nFinish reason:\n{response.candidates[0].finish_reason}")
        print(f"\nSafety ratings:\n{response.candidates[0].safety_ratings}")
        print("\nResponse text:")
        print("=" * 80)
        print(response.text)
        print("=" * 80)
        return response.text
    except Exception as e:
        print(f"Error querying Gemini: {str(e)}")
        print(traceback.format_exc())
        raise

def parse_code_blocks(solution_text):
    """Extract code blocks and their file paths from the solution text"""
    print("\nParsing code blocks from solution...")
    print(f"Solution text length: {len(solution_text)}")
    
    # First pattern: Look for (WITH CHANGES) blocks
    pattern = r'File:\s*([\w/.,-]+)\s*\(WITH CHANGES\)\n```[\w-]*\n(.*?)```'
    matches = re.finditer(pattern, solution_text, re.DOTALL)
    code_changes = []
    
    print("\nLooking for code blocks with (WITH CHANGES) marker...")
    for match in matches:
        file_path = match.group(1).strip()
        new_code = match.group(2).strip()
        print(f"\nFound code block for file: {file_path}")
        print(f"Code length: {len(new_code)}")
        print("First few lines of code:")
        print("\n".join(new_code.split("\n")[:5]))
        
        if file_path and new_code:
            if Path(file_path).is_file():
                current_content = get_file_content(file_path)
                if current_content.strip() != new_code.strip():
                    code_changes.append((file_path, new_code))
                    print(f"Changes detected in {file_path}")
                    print("Diff preview:")
                    print_diff_preview(current_content, new_code)
                else:
                    print(f"No actual changes in {file_path}")
            else:
                code_changes.append((file_path, new_code))
                print(f"New file will be created: {file_path}")
    
    # If no matches found, try fallback pattern
    if not code_changes:
        print("\nNo matches found with (WITH CHANGES) pattern, trying fallback pattern...")
        # Look for any code blocks with file paths
        pattern = r'File:\s*([\w/.,-]+)(?:\s*\([^)]*\))?\n```[\w-]*\n(.*?)```'
        matches = re.finditer(pattern, solution_text, re.DOTALL)
        
        for match in matches:
            file_path = match.group(1).strip()
            new_code = match.group(2).strip()
            print(f"\nFound code block for file: {file_path}")
            print(f"Code length: {len(new_code)}")
            print("First few lines of code:")
            print("\n".join(new_code.split("\n")[:5]))
            
            if file_path and new_code:
                if Path(file_path).is_file():
                    current_content = get_file_content(file_path)
                    if current_content.strip() != new_code.strip():
                        code_changes.append((file_path, new_code))
                        print(f"Changes detected in {file_path}")
                        print("Diff preview:")
                        print_diff_preview(current_content, new_code)
                    else:
                        print(f"No actual changes in {file_path}")
                else:
                    code_changes.append((file_path, new_code))
                    print(f"New file will be created: {file_path}")
    
    print(f"\nTotal code changes found: {len(code_changes)}")
    for file_path, code in code_changes:
        print(f"- {file_path}: {len(code)} characters")
    
    return code_changes

def print_diff_preview(current, new, context_lines=3):
    """Print a simple diff preview of the changes"""
    current_lines = current.strip().split("\n")
    new_lines = new.strip().split("\n")
    
    print("\nDiff preview:")
    for i, line in enumerate(new_lines):
        if i >= len(current_lines) or line != current_lines[i]:
            start = max(0, i - context_lines)
            end = min(len(new_lines), i + context_lines + 1)
            print(f"\nChanges around line {i + 1}:")
            for j in range(start, end):
                if j >= len(current_lines):
                    print(f"+{new_lines[j]}")
                elif j >= len(new_lines):
                    print(f"-{current_lines[j]}")
                elif new_lines[j] != current_lines[j]:
                    print(f"-{current_lines[j]}")
                    print(f"+{new_lines[j]}")
                else:
                    print(f" {new_lines[j]}")

def generate_detailed_prompt(issue, initial_response, file_paths):
    """Generate a detailed prompt including current file contents"""
    print("\nGenerating detailed prompt...")
    print(f"Files for detailed analysis: {file_paths}")
    
    # Get content of all files
    file_contents = []
    for file_path in file_paths:
        if Path(file_path).is_file():
            content = get_file_content(file_path)
            file_contents.append(f"""
File: {file_path} (CURRENT CONTENT)
```python
{content}
```
""")
            print(f"Added content of {file_path}")
    
    if not file_contents:
        print("Warning: No file contents found in the specified paths")
    
    prompt = f"""
Based on the initial analysis and the content of the relevant files, provide a detailed solution:

Issue Title: {issue.title}
Issue Body: {issue.body}

Initial Analysis:
{initial_response}

Current Files in Context:
{' '.join(file_contents)}

Please provide a complete solution following these rules EXACTLY:

1. First, explain your proposed solution in detail.
2. For each file that needs changes:
   - Show the CURRENT content using (CURRENT CONTENT) marker
   - List the specific changes you'll make
   - Show the complete NEW content using (WITH CHANGES) marker

The format must be:

File: path/to/file.py (CURRENT CONTENT)
```python
# Current content here
```

Changes to make:
- Change description 1
- Change description 2

File: path/to/file.py (WITH CHANGES)
```python
# Complete new content here with changes
```

IMPORTANT:
- Always include ALL existing code when showing changes
- Preserve all imports, comments, and functionality
- Use exact file paths from the repository
- If creating new files, list them as new files
- Make sure your solution is complete and self-contained
"""
    
    print(f"Generated prompt with {len(file_contents)} files included")
    return prompt