import os
from github import Github
from datetime import datetime, timezone
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
