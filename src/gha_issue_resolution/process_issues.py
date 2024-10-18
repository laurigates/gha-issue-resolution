import os
import json
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

def get_file_content(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
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

def create_pull_request(issue, solution):
    # Create a new branch
    base_branch = repo.default_branch
    new_branch_base = f"fix-issue-{issue.number}"
    new_branch = new_branch_base
    sb = repo.get_branch(base_branch)
    
    # Check if branch exists and create a unique name if it does
    branch_exists = True
    counter = 1
    while branch_exists:
        try:
            repo.get_branch(new_branch)
            new_branch = f"{new_branch_base}-{counter}"
            counter += 1
        except:
            branch_exists = False

    # Create the new branch
    repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=sb.commit.sha)

    # Parse the solution to extract file changes
    changes = parse_solution_for_changes(solution)

    # Commit changes
    for file_path, new_content in changes.items():
        try:
            try:
                file = repo.get_contents(file_path, ref=new_branch)
                repo.update_file(file_path, f"Fix for issue #{issue.number}", new_content, file.sha, branch=new_branch)
            except:
                # File doesn't exist, so create it
                repo.create_file(file_path, f"Fix for issue #{issue.number}", new_content, branch=new_branch)
        except Exception as e:
            print(f"Error updating file {file_path}: {str(e)}")

    # Create pull request
    pr = repo.create_pull(
        title=f"Fix for issue #{issue.number}",
        body=f"This pull request addresses issue #{issue.number}.\n\nProposed solution:\n\n{solution}",
        head=new_branch,
        base=base_branch
    )
    
    return pr.html_url

def parse_solution_for_changes(solution):
    changes = {}
    current_file = None
    current_content = []

    for line in solution.split('\n'):
        if line.startswith('File: '):
            if current_file:
                changes[current_file] = '\n'.join(current_content)
            current_file = line.split(': ')[1].strip()
            current_content = []
        elif current_file:
            current_content.append(line)

    if current_file:
        changes[current_file] = '\n'.join(current_content)

    return changes

def process_issue(issue):
    try:
        # Check if the issue has at least one comment
        comments = list(issue.get_comments())
        if len(comments) == 0:
            print(f"Issue #{issue.number} has no comments. Skipping.")
            return

        repo_structure = get_repo_structure()
        
        # Get content of files mentioned in the issue or comments
        file_contents = ""
        all_text = issue.body + ' '.join([comment.body for comment in comments])
        for file in Path('.').rglob('*'):
            if file.is_file() and '.git' not in file.parts and str(file) in all_text:
                file_contents += f"\nContent of {file}:\n```\n{get_file_content(file)}\n```\n"

        initial_prompt = f"""
        Given the following GitHub issue, comments, repository structure, and relevant file contents, suggest a solution:

        Issue Title: {issue.title}
        Issue Body: {issue.body}

        Comments:
        {' '.join([comment.body for comment in comments])}

        Repository Structure:
        {repo_structure}

        Relevant File Contents:
        {file_contents}

        Please provide the following:
        1. A brief analysis of the issue and comments.
        2. A list of files that need to be modified to resolve this issue.
        3. A detailed solution, including specific code changes for each file.

        Format your response in Markdown, and use the following format for file changes:
        
        File: [filename]
        [entire new content of the file]

        Repeat this for each file that needs changes.
        """
        
        solution = query_gemini(initial_prompt)
        
        # Create a pull request with the proposed changes
        pr_url = create_pull_request(issue, solution)
        
        comment_body = f"""
        ## AI-generated pull request

        Based on the issue description and comments, an AI assistant has generated a potential solution and created a pull request.

        You can view the proposed changes here: {pr_url}

        Please review the changes carefully and provide feedback or merge if appropriate.
        This is an AI-generated solution and may require human validation and testing before implementation.
        """
        
        issue.create_comment(comment_body)
        print(f"Created pull request for issue #{issue.number}")
    except Exception as e:
        error_message = f"Error processing issue #{issue.number}: {str(e)}"
        print(error_message)
        try:
            issue.create_comment(f"An error occurred while processing this issue: {error_message}")
        except:
            print(f"Failed to comment on issue #{issue.number} about the error.")

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