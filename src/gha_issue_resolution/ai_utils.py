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
                    When suggesting code changes, you MUST follow these rules:
                    1. First explain your changes in plain English
                    2. Then for each file you want to modify:
                       - Show the current file content
                       - Explain the specific changes you'll make
                       - Show the complete new file content with your changes integrated
                    3. Use this exact format for code blocks:
                       
                       File: path/to/file.py (CURRENT CONTENT)
                       ```python
                       # Current file content here
                       ```
                       
                       Changes to make:
                       - Description of change 1
                       - Description of change 2
                       
                       File: path/to/file.py (WITH CHANGES)
                       ```python
                       # Complete file content with changes
                       ```
                    
                    4. Make sure to incorporate all existing code when showing the changed version
                    5. Preserve all imports, comments, and functionality not related to your changes
                    """,
                    prompt
                ]
            })
        ])
        print(f"\nUsage metadata:\n{response.prompt_feedback}")
        print(f"\nFinish reason:\n{response.candidates[0].finish_reason}")
        print(f"\nSafety ratings:\n{response.candidates[0].safety_ratings}")
        return response.text
    except Exception as e:
        print(f"Error querying Gemini: {str(e)}")
        print(traceback.format_exc())
        raise

def parse_code_blocks(solution_text):
    """Extract code blocks and their file paths from the solution text"""
    print("\nParsing code blocks from solution...")
    print(f"Solution text length: {len(solution_text)}")
    
    # Look for code blocks marked as "WITH CHANGES"
    pattern = r'File:\s*([\w/.,-]+)\s*\(WITH CHANGES\)\n```[\w-]*\n(.*?)```'
    matches = re.finditer(pattern, solution_text, re.DOTALL)
    code_changes = []
    
    for match in matches:
        file_path = match.group(1).strip()
        new_code = match.group(2).strip()
        print(f"\nFound code block for file: {file_path}")
        print(f"New code length: {len(new_code)}")
        
        if file_path and new_code:
            # Verify the file exists and changes are different
            if Path(file_path).is_file():
                current_content = get_file_content(file_path)
                if current_content.strip() != new_code.strip():
                    code_changes.append((file_path, new_code))
                    print(f"Changes detected in {file_path}")
                else:
                    print(f"No actual changes in {file_path}")
            else:
                # New file
                code_changes.append((file_path, new_code))
                print(f"New file will be created: {file_path}")
    
    print(f"\nTotal code changes found: {len(code_changes)}")
    for file_path, code in code_changes:
        print(f"- {file_path}: {len(code)} characters")
    
    return code_changes

def generate_detailed_prompt(issue, initial_response, file_paths):
    """Generate a detailed prompt including current file contents"""
    file_contents = ""
    for file_path in file_paths[:5]:  # Limit to 5 files
        if Path(file_path).is_file():
            content = get_file_content(file_path)
            file_contents += f"""
            Current content of {file_path}:
            ```
            {content}
            ```
            """
            print(f"Added content of {file_path}")

    return f"""
    Based on the initial analysis and the content of the relevant files, provide a detailed solution:

    Issue Title: {issue.title}
    Issue Body: {issue.body}

    Initial Analysis and Suggestion:
    {initial_response}

    Current File Contents:
    {file_contents}

    Please provide:
    1. A detailed explanation of your proposed solution.
    2. For each file that needs changes:
       - Show the current content
       - Explain the specific changes you'll make
       - Show the complete new content with your changes
       Use the exact format specified with (CURRENT CONTENT) and (WITH CHANGES) markers.
    3. An explanation of why these changes will resolve the issue.
    4. Any potential side effects or considerations.

    Remember:
    - Use the exact format shown above for code blocks
    - Include ALL existing code when showing the changed version
    - Preserve all imports, comments, and unrelated functionality
    - Make sure the changed version is a complete, working file
    """
