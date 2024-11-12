"""Module for processing GitHub issues"""

from gha_issue_resolution.comment_handler import (
    get_bot_comments,
    create_analysis_comment,
    process_comment
)

def process_issue(repo, issue):
    """Process a GitHub issue"""
    print(f"\nProcessing issue #{issue.number}: {issue.title}")
    print(f"Issue body: {issue.body}")
    
    # Get any existing bot comments
    bot_comments = get_bot_comments(issue)
    
    # Get the latest comment that triggered this run
    trigger_comment = getattr(issue, 'comment', None)
    
    # If it's a new issue or has no analysis, create initial analysis
    if not bot_comments:
        print("\nNo existing analysis found, creating initial analysis...")
        create_analysis_comment(issue)
        return
    
    # If triggered by a comment, process it
    if trigger_comment:
        process_comment(repo, issue, trigger_comment)