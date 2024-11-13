"""Main entry point for GitHub Action"""
import os
import sys
from github import Github
from gha_issue_resolution.issue_processor import process_issue

def main():
    """Main function"""
    try:
        # Get environment variables
        token = os.environ['GITHUB_TOKEN']
        event_name = os.environ.get('GITHUB_EVENT_NAME')
        event_action = os.environ.get('GITHUB_EVENT_ACTION')
        
        print(f"Event type: {event_name}")
        print(f"Event action: {event_action}")
        
        # Initialize GitHub client
        gh = Github(token)
        
        # Get repository
        repo_name = os.environ['GITHUB_REPOSITORY']
        repo = gh.get_repo(repo_name)
        
        # Get issue number from event payload
        if event_name == 'issues' and event_action == 'opened':
            issue_number = os.environ['GITHUB_EVENT_NUMBER']
        elif event_name == 'issue_comment' and event_action == 'created':
            issue_number = os.environ['GITHUB_EVENT_ISSUE_NUMBER']
        else:
            print(f"Unsupported event: {event_name} {event_action}")
            sys.exit(1)
        
        # Get issue
        issue = repo.get_issue(number=int(issue_number))
        
        # Process issue
        process_issue(repo, issue)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()