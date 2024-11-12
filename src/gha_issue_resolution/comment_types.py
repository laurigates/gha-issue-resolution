import os
from github.Issue import Issue
from github.IssueComment import IssueComment
from gha_issue_resolution.comment_handler import (
    create_analysis_comment, get_bot_comments, get_human_feedback,
    create_response_comment
)
from gha_issue_resolution.pr_handler import create_pr_from_analysis

# Command triggers
TRIGGER_PR_COMMENT = "/create-pr"
TRIGGER_UPDATE_COMMENT = "/update"

def check_triggers(comment):
    """Check if a comment contains trigger commands"""
    if not comment or not hasattr(comment, 'body'):
        return False, False
    
    body = comment.body.strip().lower()
    create_pr = TRIGGER_PR_COMMENT.lower() in body
    update_analysis = TRIGGER_UPDATE_COMMENT.lower() in body
    
    return create_pr, update_analysis

def process_issue(repo, issue):
    """Process a GitHub issue"""
    print(f"\nProcessing issue #{issue.number}: {issue.title}")
    print(f"Issue body: {issue.body}")
    
    # Get any existing bot comments
    bot_comments = get_bot_comments(issue)
    
    # Get the latest comment that triggered this run
    trigger_comment = None
    if hasattr(issue, 'comment'):
        trigger_comment = issue.comment
        print(f"\nTrigger comment body: {trigger_comment.body}")
    
    # Check if this is a new issue or needs initial analysis
    if not bot_comments:
        print("\nNo existing analysis found, creating initial analysis...")
        analysis_comment = create_analysis_comment(issue)
        bot_comments = [analysis_comment]
        return
    
    # Get the most recent analysis
    latest_analysis = bot_comments[-1]
    
    # If triggered by a comment, check for triggers
    if trigger_comment:
        create_pr, update_analysis = check_triggers(trigger_comment)
        
        if create_pr:
            print("\nPull request creation triggered...")
            create_pr_from_analysis(repo, issue, latest_analysis)
        elif update_analysis:
            print("\nUpdated analysis triggered...")
            new_analysis = create_analysis_comment(issue)
            print(f"Created new analysis comment: {new_analysis.html_url}")
        else:
            # Respond to the comment
            print("\nGenerating response to comment...")
            create_response_comment(issue, trigger_comment)