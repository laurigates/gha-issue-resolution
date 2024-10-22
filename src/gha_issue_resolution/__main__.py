import os
import json
from pathlib import Path
import google.generativeai as genai
from github import Github
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai.types import GenerationConfig
import base64
import re

def setup_github():
    """Setup GitHub client and get repository"""
    try:
        g = Github(os.environ['GITHUB_TOKEN'])
        repo = g.get_repo(os.environ['GITHUB_REPOSITORY'])
        return g, repo
    except KeyError as e:
        print(f"Missing environment variable: {e}")
        raise
    except Exception as e:
        print(f"Error setting up GitHub client: {e}")
        raise

# Setup GitHub client
g, repo = setup_github()

# Setup Gemini API
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
genai.configure(api_key=GEMINI_API_KEY)

# Set a large default max token limit
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '8192'))

# Specify the Gemini Flash model
MODEL_ID = 'gemini-1.5-flash-002'

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
        return f"Error reading file: {str(e)}"

def query_gemini(prompt):
    model = genai.GenerativeModel(
        MODEL_ID,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    response = model.generate_content([
        genai.types.ContentDict({
            'role': 'user',
            'parts': [
                "You are an AI assistant specialized in analyzing GitHub issues and suggesting solutions. "
                "Your task is to provide detailed, actionable advice for resolving the given issue.",
                prompt
            ]
        })
    ])
    print(f"\nUsage metadata:\n{response.prompt_feedback}")
    print(f"\nFinish reason:\n{response.candidates[0].finish_reason}")
    print(f"\nSafety ratings:\n{response.candidates[0].safety_ratings}")
    return response.text

def parse_code_blocks(solution_text):
    """Extract code blocks and their file paths from the solution text"""
    # Pattern to match markdown code blocks with optional file paths
    pattern = r'```(?:[\w-]+)?\s*(?:File:\s*([\w/.,-]+))?\n(.*?)```'
    matches = re.finditer(pattern, solution_text, re.DOTALL)
    
    code_changes = []
    for match in matches:
        file_path = match.group(1)
        code = match.group(2).strip()
        if file_path:
            code_changes.append((file_path, code))
    return code_changes

def create_branch(repo, base_branch='main'):
    """Create a new branch for the changes"""
    try:
        base_ref = repo.get_git_ref(f"heads/{base_branch}")
        branch_name = f"ai-suggestion-{os.urandom(4).hex()}"
        repo.create_git_ref(f"refs/heads/{branch_name}", base_ref.object.sha)
        return branch_name
    except Exception as e:
        print(f"Error creating branch: {e}")
        raise

def update_file(repo, file_path, content, branch, commit_message):
    """Update or create a file in the repository"""
    try:
        # Try to get existing file
        try:
            file = repo.get_contents(file_path, ref=branch)
            repo.update_file(
                file_path,
                commit_message,
                content,
                file.sha,
                branch=branch
            )
        except Exception:
            # File doesn't exist, create it
            repo.create_file(
                file_path,
                commit_message,
                content,
                branch=branch
            )
    except Exception as e:
        print(f"Error updating file {file_path}: {e}")
        raise

def create_pull_request(repo, issue, solution_text, code_changes):
    """Create a pull request with the suggested changes"""
    try:
        # Create a new branch
        branch_name = create_branch(repo)
        
        # Apply each code change
        for file_path, new_content in code_changes:
            update_file(
                repo,
                file_path,
                new_content,
                branch_name,
                f"AI suggestion: Update {file_path}"
            )
        
        # Create pull request
        pr = repo.create_pull(
            title=f"AI suggestion for issue #{issue.number}",
            body=f"""This pull request addresses issue #{issue.number}

{solution_text}

This is an AI-generated pull request. Please review the changes carefully before merging.
            """,
            base="main",
            head=branch_name
        )
        
        # Link PR to issue
        issue.create_comment(f"I've created a pull request with suggested changes: {pr.html_url}")
        
        return pr
    except Exception as e:
        print(f"Error creating pull request: {e}")
        raise

def process_issue(issue):
    # Check if we've already commented on this issue
    for comment in issue.get_comments():
        if "AI-generated suggestion" in comment.body:
            print(f"Already commented on issue #{issue.number}. Skipping.")
            return

    repo_structure = get_repo_structure()
    initial_prompt = f"""
    Analyze this GitHub issue and suggest a solution based on the repository structure:
    
    Issue Title: {issue.title}
    Issue Body: {issue.body}
    
    Repository Structure:
    {repo_structure}
    
    Provide:
    1. A brief analysis of the issue.
    2. A list of files that are likely relevant to this issue (up to 5 files).
    3. An initial approach for solving this issue.
    """
    
    initial_response = query_gemini(initial_prompt)
    
    # Extract file paths from the initial response
    file_paths = [line.split()[-1] for line in initial_response.split('\n') if line.startswith('-') and '.' in line]
    
    # Get content of identified files
    file_contents = ""
    for file_path in file_paths[:5]:  # Limit to 5 files
        if Path(file_path).is_file():
            file_contents += f"\nContent of {file_path}:\n```\n{get_file_content(file_path)}\n```\n"

    # Second prompt with file contents and request for specific code changes
    detailed_prompt = f"""
    Based on the initial analysis and the content of the relevant files, provide a detailed solution:

    Issue Title: {issue.title}
    Issue Body: {issue.body}

    Initial Analysis and Suggestion:
    {initial_response}

    Relevant File Contents:
    {file_contents}

    Please provide:
    1. A detailed explanation of the solution.
    2. Specific code changes needed, using markdown code blocks with 'File:' headers for each change, like this:
       ```python
       File: path/to/file.py
       # Your code here
       ```
    3. An explanation of why these changes would resolve the issue.
    4. Any potential side effects or considerations.

    Make sure to include the complete file content for any files that need changes, not just the changed portions.
    """

    detailed_solution = query_gemini(detailed_prompt)
    
    # Extract code changes from the solution
    code_changes = parse_code_blocks(detailed_solution)
    
    comment_body = f"""
    ## AI-generated suggestion

    Here's a potential solution to this issue, generated by an AI assistant:

    {detailed_solution}

    I'll create a pull request with these suggested changes.
    This is an AI-generated response and requires human validation and testing before implementation.
    """
    
    issue.create_comment(comment_body)
    print(f"Commented on issue #{issue.number}")
    
    if code_changes:
        pr = create_pull_request(repo, issue, detailed_solution, code_changes)
        print(f"Created pull request #{pr.number}")
    else:
        print("No code changes found in the solution")

def handle_event():
    """Parse and handle GitHub event"""
    event_name = os.environ.get('GITHUB_EVENT_NAME')
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    
    if not event_name or not event_path:
        print("No GitHub event information found")
        return None, None
    
    try:
        with open(event_path, 'r') as f:
            event_data = json.load(f)
            print(f"Event data: {json.dumps(event_data, indent=2)}")
            return event_name, event_data
    except Exception as e:
        print(f"Error reading event data: {e}")
        return None, None

def main():
    print(f"Starting Issue Resolution with Gemini Flash (Model: {MODEL_ID})")
    
    # Handle GitHub event
    event_name, event_data = handle_event()
    
    if event_name == 'issues':
        action = event_data.get('action')
        if action in ['opened', 'reopened', 'edited']:
            issue_number = event_data['issue']['number']
            print(f"Processing issue #{issue_number}")
            issue = repo.get_issue(issue_number)
            process_issue(issue)
        else:
            print(f"Ignoring issue event with action: {action}")
            
    elif event_name == 'pull_request':
        print("Pull request event detected, but no action needed")
        
    elif event_name:
        print(f"Unsupported event type: {event_name}")
        
    else:
        print("No specific event detected, checking for open issues...")
        open_issues = repo.get_issues(state='open')
        for issue in open_issues:
            process_issue(issue)

    print("Finished Issue Resolution with Gemini Flash")

if __name__ == "__main__":
    main()
