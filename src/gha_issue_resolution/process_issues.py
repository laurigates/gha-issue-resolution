import os
import requests
from github import Github
from pathlib import Path

# Setup GitHub client
g = Github(os.environ['GITHUB_TOKEN'])
repo = g.get_repo(os.environ['GITHUB_REPOSITORY'])

# Setup Gemini API
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

def get_repo_structure():
    structure = ""
    for file in Path('.').rglob('*'):
        if file.is_file() and '.git' not in file.parts:
            structure += f"- {file}\n"
    return structure

def get_file_content(file_path, max_lines=50):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            return ''.join(lines[:max_lines])
    except Exception as e:
        return f"Error reading file: {str(e)}"

def query_gemini(prompt):
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "contents": [{"parts":[{"text": prompt}]}],
    }
    response = requests.post(
        f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
        headers=headers,
        json=data
    )
    return response.json()['candidates'][0]['content']['parts'][0]['text']

def process_issue(issue):
    # Check if we've already commented on this issue
    for comment in issue.get_comments():
        if "AI-generated suggestion" in comment.body:
            print(f"Already commented on issue #{issue.number}. Skipping.")
            return

    repo_structure = get_repo_structure()
    initial_prompt = f"""
    Given the following GitHub issue and repository structure, suggest a solution:

    Issue Title: {issue.title}
    Issue Body: {issue.body}

    Repository Structure:
    {repo_structure}

    Please provide the following:
    1. A brief analysis of the issue.
    2. A list of files that are likely relevant to this issue. Don't limit yourself to a specific number, but be judicious and only include files that are directly relevant.
    3. An initial suggestion for how to approach solving this issue.

    Format your response in Markdown for better readability.
    """
    
    initial_response = query_gemini(initial_prompt)
    
    # Extract file paths from the initial response
    file_paths = [line.split()[-1] for line in initial_response.split('\n') if line.startswith('-') and '.' in line]
    
    # Get content of identified files
    file_contents = ""
    for file_path in file_paths:
        if Path(file_path).is_file():
            file_contents += f"\nContent of {file_path}:\n```\n{get_file_content(file_path)}\n```\n"

    # Second prompt with file contents
    detailed_prompt = f"""
    Based on the initial analysis and the content of the relevant files, provide a more detailed solution:

    Issue Title: {issue.title}
    Issue Body: {issue.body}

    Initial Analysis and Suggestion:
    {initial_response}

    Relevant File Contents:
    {file_contents}

    Please provide:
    1. A detailed solution to the issue, including specific code changes if applicable.
    2. An explanation of why these changes would resolve the issue.
    3. Any potential side effects or considerations to keep in mind when implementing this solution.

    Format your response in Markdown for better readability.
    """

    detailed_solution = query_gemini(detailed_prompt)
    
    comment_body = f"""
    ## AI-generated suggestion

    Here's a potential solution to this issue, generated by an AI assistant:

    {detailed_solution}

    Please review this suggestion and let me know if you need any clarification or have any questions.
    This is an AI-generated response and may require human validation and testing before implementation.
    """
    
    issue.create_comment(comment_body)
    print(f"Commented on issue #{issue.number}")

def main():
    # Check if we're running in response to an issue event
    if 'GITHUB_EVENT_NAME' in os.environ and os.environ['GITHUB_EVENT_NAME'] == 'issues':
        with open(os.environ['GITHUB_EVENT_PATH']) as f:
            event_data = json.load(f)
        issue_number = event_data['issue']['number']
        issue = repo.get_issue(issue_number)
        process_issue(issue)
    else:
        # If not an issue event, process all open issues
        open_issues = repo.get_issues(state='open')
        for issue in open_issues:
            process_issue(issue)

if __name__ == "__main__":
    main()
