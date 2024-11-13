"""Module for creating and managing pull requests"""
from typing import List, Tuple, Optional, Union
from github.Repository import Repository
from github.Issue import Issue
from github.IssueComment import IssueComment
from github.PullRequest import PullRequest
import os
from datetime import datetime, timezone
import traceback
from gha_issue_resolution.ai_utils import parse_code_blocks

def create_branch(repo: Repository, base_branch: str = 'main') -> str:
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

def update_file(
    repo: Repository, 
    file_path: str, 
    content: str, 
    branch: str, 
    commit_message: str
) -> None:
    """Update or create a file in the repository"""
    try:
        print(f"Updating file: {file_path} on branch: {branch}")
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
            print(f"File {file_path} doesn't exist, creating new file. Error: {str(e)}")
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

def create_pull_request(
    repo: Repository, 
    issue: Issue, 
    solution_text: Union[str, IssueComment],
    code_changes: Optional[List[Tuple[str, str]]] = None
) -> Optional[PullRequest]:
    """Create a pull request with the suggested changes"""
    try:
        print("\nCreating pull request...")
        
        # Get code changes if not provided
        if code_changes is None:
            solution_body = solution_text.body if hasattr(solution_text, 'body') else solution_text
            code_changes = parse_code_blocks(solution_body)
        
        if not code_changes:
            print("No code changes found in the analysis")
            return None
        
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
        error_comment = f"""
        I encountered an error while trying to create the pull request:
        ```
        {str(e)}
        ```
        Please check the repository permissions and settings.
        """
        issue.create_comment(error_comment)
        raise
