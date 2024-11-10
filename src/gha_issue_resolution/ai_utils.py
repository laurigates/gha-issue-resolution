import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai.types import GenerationConfig
import traceback
import re
from pathlib import Path
from typing import List, Tuple
import tempfile

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

def create_temp_file(content: str, suffix: str = '.txt') -> str:
    """Create a temporary file with given content"""
    temp = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
    try:
        temp.write(content)
        temp.close()
        return temp.name
    except Exception as e:
        print(f"Error creating temp file: {e}")
        if os.path.exists(temp.name):
            os.unlink(temp.name)
        raise

def cleanup_temp_file(filepath: str):
    """Safely delete temporary file"""
    try:
        if os.path.exists(filepath):
            os.unlink(filepath)
    except Exception as e:
        print(f"Warning: Failed to delete temporary file {filepath}: {e}")

def prepare_file_for_upload(file_path: str) -> str:
    """Read file content and prepare it for upload"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            if not content.strip():
                return None
            return content
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def query_gemini(prompt, file_contents: List[Tuple[str, str]] = None):
    """Query Gemini API using File API for large content"""
    try:
        model = genai.GenerativeModel(
            MODEL_ID,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )

        # If we have file contents, create temporary files and use File API
        temp_files = []
        content_parts = []

        if isinstance(prompt, str):
            content_parts.append(prompt)
        else:
            content_parts.extend(prompt)

        if file_contents:
            for filepath, content in file_contents:
                if content:
                    temp_path = create_temp_file(content)
                    temp_files.append(temp_path)
                    file_obj = genai.upload_file(temp_path)
                    content_parts.extend([
                        f"\nFile: {filepath}",
                        file_obj
                    ])

        try:
            response = model.generate_content(content_parts)
            print(f"\nUsage metadata:\n{response.prompt_feedback}")
            print(f"\nFinish reason:\n{response.candidates[0].finish_reason}")
            print(f"\nSafety ratings:\n{response.candidates[0].safety_ratings}")
            return response.text
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                cleanup_temp_file(temp_file)

    except Exception as e:
        print(f"Error querying Gemini: {str(e)}")
        print(traceback.format_exc())
        raise

def analyze_issue(issue, relevant_files: List[str]) -> str:
    """Analyze issue using File API for file contents"""
    print(f"\nAnalyzing issue with {len(relevant_files)} relevant files...")
    
    # Prepare files and their contents
    file_contents = []
    for file_path in relevant_files:
        if Path(file_path).is_file():
            content = prepare_file_for_upload(file_path)
            if content:
                file_contents.append((file_path, content))
    
    if not file_contents:
        return "No relevant files found for analysis."
    
    prompt = f"""Analyze this GitHub issue and suggest a solution based on the repository content.
    
Issue Title: {issue.title}
Issue Body: {issue.body}

Please provide:
1. A detailed analysis of the issue and what needs to be changed
2. List the specific files that need modification and explain why
3. For each file that needs changes, provide:
   a. The current state and why it needs to change
   b. The specific changes required
   c. Complete code for the changes using this format:
   
   File: path/to/file.py (CURRENT CONTENT)
   ```python
   # Current content here
   ```
   
   Changes to make:
   - Detailed description of change 1
   - Detailed description of change 2
   
   File: path/to/file.py (WITH CHANGES)
   ```python
   # Complete new content with changes
   ```

4. Explain how these changes will resolve the issue
5. Note any potential side effects or additional considerations
"""
    
    return query_gemini(prompt, file_contents)

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
        
        if file_path and new_code:
            if Path(file_path).is_file():
                current_content = prepare_file_for_upload(file_path)
                if current_content and current_content.strip() != new_code.strip():
                    code_changes.append((file_path, new_code))
                    print(f"Changes detected in {file_path}")
            else:
                code_changes.append((file_path, new_code))
                print(f"New file will be created: {file_path}")
    
    print(f"\nTotal code changes found: {len(code_changes)}")
    return code_changes
