import os
import json
from pathlib import Path
import google.generativeai as genai
from github import Github
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai.types import GenerationConfig
import base64
import re
from datetime import datetime, timedelta, timezone
import traceback

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
        print(traceback.format_exc())
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
        print(f"Error reading file {file_path}: {str(e)}")
        print(traceback.format_exc())
        return f"Error reading file: {str(e)}"

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
                    1. Always include the complete file content, not just the changes
                    2. Use markdown code blocks for each file change
                    3. Start each code block with 'File: filename.ext' on its own line
                    4. Make sure to use the correct file paths
                    
                    Example format:
                    File: src/example.py
                    ```python
                    # Complete file content here
                    ```
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
    
    # First look for the explicit format we requested
    pattern = r'File:\s*([\w/.,-]+)\n```[\w-]*\n(.*?)```'
    matches = re.finditer(pattern, solution_text, re.DOTALL)
    code_changes = []
    
    for match in matches:
        file_path = match.group(1).strip()
        code = match.group(2).strip()
        print(f"\nFound code block for file: {file_path}")
        print(f"Code length: {len(code)}")
        if file_path and code:
            code_changes.append((file_path, code))
    
    # If no matches found, try alternative formats
    if not code_changes:
        print("\nNo matches found with primary pattern, trying alternative patterns...")
        # Look for code blocks with file paths in the preceding text
        lines = solution_text.split('\n')
        current_file = None
        current_code = []
        in_code_block = False
        
        for line in lines:
            # Check for file path indicators
            file_match = re.search(r'(?:in|for|to|update|create|modify|file:?)\s+[`"]?([\w/.,-]+\.[a-zA-Z]+)[`"]?', line, re.IGNORECASE)
            if file_match and not in_code_block:
                if current_file and current_code:
                    code_changes.append((current_file, '\n'.join(current_code)))
                current_file = file_match.group(1)
                current_code = []
                print(f"\nFound file reference: {current_file}")
            
            # Track code blocks
            if line.startswith('```'):
                in_code_block = not in_code_block
                continue
            
            if in_code_block and current_file:
                current_code.append(line)
        
        # Add the last file if exists
        if current_file and current_code:
            code_changes.append((current_file, '\n'.join(current_code)))
    
    print(f"\nTotal code changes found: {len(code_changes)}")
    for file_path, code in code_changes:
        print(f"- {file_path}: {len(code)} characters")
    
    return code_changes

def create_branch(repo, base_branch='main'):
    """Create a new branch for the changes"""
    try:
        # Try 'main' first, then 'master' if 'main' fails
        try:
            base_ref = repo.get_git_ref(f"heads/{base_branch}")
        except:
            base_branch = 'master'
            base_ref = repo.get_git_ref(f"heads/{base_branch}")
            
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
        branch_name = f"ai-suggestion-{timestamp}-{os.urandom(2).hex()}"
        repo.create_git_ref(f"refs/heads/{branch_name}", base_ref.object.sha)
        print(f"Created branch: {branch_name} from {base_branch}")
        return branch_name
    except Exception as e:
        print(f"Error creating branch: {str(e)}")
        print(traceback.format_exc())
        raise

def update_file(repo, file_path, content, branch, commit_message):
    """Update or create a file in the repository"""
    try:
        print(f"Attempting to update file: {file_path} on branch: {branch}")
        print(f"Content length: {len(content)}")
        
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
            print(f"Updated existing file: {file_path}")
        except Exception as e:
            print(f"File {file_path} doesn't exist, creating new file. Error was: {str(e)}")
            repo.create_file(
                file_path,
                commit_message,
                content,
                branch=branch
            )
            print(f"Created new file: {file_path}")
    except Exception as e:
        print(f"Error updating file {file_path}: {str(e)}")
        print(traceback.format_exc())
        raise

def create_pull_request(repo, issue, solution_text, code_changes):
    """Create a pull request with the suggested changes"""
    try:
        print("\nCreating pull request...")
        print(f"Number of code changes to apply: {len(code_changes)}")
        
        # Create a new branch
        branch_name = create_branch(repo)
        
        # Apply each code change
        for file_path, new_content in code_changes:
            print(f"\nProcessing changes for file: {file_path}")
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
            base=repo.default_branch,
            head=branch_name
        )
        
        print(f"Created pull request: {pr.html_url}")
        
        # Link PR to issue
        comment = issue.create_comment(f"I've created a pull request with suggested changes: {pr.html_url}")
        print(f"Added comment to issue: {comment.html_url}")
        
        return pr
    except Exception as e:
        print(f"Error creating pull request: {str(e)}")
        print(traceback.format_exc())
        raise

def get_bot_comments(issue):
    """Get all AI-generated comments on the issue"""
    bot_comments = []
    for comment in issue.get_comments():
        if "AI-generated suggestion" in comment.body:
            bot_comments.append(comment)
    return bot_comments

def process_issue(issue):
    print(f"\nProcessing issue #{issue.number}: {issue.title}")
    print(f"Issue body: {issue.body}")
    
    # Get any existing bot comments
    bot_comments = get_bot_comments(issue)
    
    # Check if issue needs analysis comment
    needs_analysis = not bot_comments
    
    if needs_analysis:
        print("\nGenerating initial analysis...")
        # Generate and post initial analysis
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
        print(f"\nIdentified relevant files: {file_paths}")
        
        # Get content of identified files
        file_contents = ""
        for file_path in file_paths[:5]:  # Limit to 5 files
            if Path(file_path).is_file():
                content = get_file_content(file_path)
                file_contents += f"\nContent of {file_path}:\n```\n{content}\n```\n"
                print(f"Added content of {file_path}")

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
        2. Specific code changes needed. For each file that needs changes, provide the COMPLETE file content (not just the changes) in this exact format:
           
           File: path/to/file.py
           ```python
           # Complete file content here
           ```

        3. An explanation of why these changes would resolve the issue.
        4. Any potential side effects or considerations.

        Remember: Always include the COMPLETE file content for any files that need changes, not just the modified portions.
        """

        print("\nGenerating detailed solution...")
        detailed_solution = query_gemini(detailed_prompt)
        
        comment_body = f"""
        ## AI-generated suggestion

        Here's a potential solution to this issue, generated by an AI assistant:

        {detailed_solution}

        I can create a pull request with these suggested changes. Please review the suggestion and add any additional comments or requirements.
        This is an AI-generated response and requires human validation and testing before implementation.
        """
        
        comment = issue.create_comment(comment_body)
        print(f"\nAdded initial analysis comment: {comment.html_url}")
        bot_comments = [comment]  # Update bot_comments with the new comment
    
    # Get the most recent bot comment
    latest_bot_comment = bot_comments[-1]
    
    # Look for additional human comments after the last bot comment
    all_comments = list(issue.get_comments())
    last_bot_index = all_comments.index(latest_bot_comment)
    human_feedback = []
    for comment in all_comments[last_bot_index + 1:]:
        if "AI-generated suggestion" not in comment.body:
            human_feedback.append(comment.body)
    
    # Generate pull request if there's a solution in the bot comments
    print("\nExtracting code changes from previous analysis...")
    code_changes = parse_code_blocks(latest_bot_comment.body)
    
    if code_changes:
        print(f"\nFound {len(code_changes)} code changes to implement")
        
        if human_feedback:
            # If there's human feedback, generate an updated solution
            feedback_prompt = f"""
            Please review the previous solution and the human feedback to generate an updated solution.
            
            Previous solution:
            {latest_bot_comment.body}
            
            Human feedback:
            {'\n'.join(human_feedback)}
            
            Provide an updated solution incorporating the feedback, using the same format as before.
            Make sure to include complete file contents in the code blocks.
            """
            
            print("\nGenerating updated solution based on feedback...")
            updated_solution = query_gemini(feedback_prompt)
            updated_code_changes = parse_code_blocks(updated_solution)
            
            if updated_code_changes:
                code_changes = updated_code_changes
                print(f"Using updated solution with {len(code_changes)} code changes")
        
        try:
            pr = create_pull_request(repo, issue, latest_bot_comment.body, code_changes)
            print(f"Created pull request #{pr.