"""Main entry point for GitHub Action"""
import os
import sys
import json
from github import Github
from gha_issue_resolution.issue_processor import process_issue

def get_event_data():
    """Get GitHub event data from environment"""
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    if not event_path:
        raise ValueError("GITHUB_EVENT_PATH not set")
    
    with open(event_path, 'r') as f:
        return json.load(f)

def main():
    """Main function"""
    try:
        # Get environment variables
        token = os.environ['GITHUB_TOKEN']
        event_name = os.environ.get('GITHUB_EVENT_NAME')
        
        print(f"Event type: {event_name}")
        
        # Get event data
        event_data = get_event_data()
        
        # Initialize GitHub client
        gh = Github(token)
        
        # Get repository
        repo_name = os.environ['GITHUB_REPOSITORY']
        repo = gh.get_repo(repo_name)
        
        # Get issue number based on event type
        if event_name == 'issues':
            issue_number = event_data['issue']['number']
            print(f"Processing issue #{issue_number}")
        elif event_name == 'issue_comment':
            issue_number = event_data['issue']['number']
            print(f"Processing comment on issue #{issue_number}")
        else:
            print(f"Unsupported event: {event_name}")
            sys.exit(1)
        
        # Get issue
        issue = repo.get_issue(number=int(issue_number))
        
        # If this is a comment event, attach the comment to the issue object
        if event_name == 'issue_comment':
            issue.comment = event_data['comment']
            print(f"Comment body: {issue.comment['body']}")
        
        # Process issue
        process_issue(repo, issue)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()