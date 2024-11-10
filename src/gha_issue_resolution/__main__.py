import os
import json
from pathlib import Path
import traceback

from gha_issue_resolution.github_utils import setup_github
from gha_issue_resolution.ai_utils import setup_ai
from gha_issue_resolution.issue_processor import process_issue

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
        print(f"Error reading event data: {str(e)}")
        print(traceback.format_exc())
        return None, None

def main():
    print("\nStarting Issue Resolution with Gemini Flash")
    
    try:
        # Setup GitHub client and AI
        g, repo = setup_github()
        setup_ai()
        
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

    except Exception as e:
        print(f"Error in main process: {str(e)}")
        print(traceback.format_exc())
        raise
        
    print("Finished Issue Resolution with Gemini Flash")

if __name__ == "__main__":
    main()
