"""Main module for handling GitHub issue comments"""

from github.Issue import Issue
from github.IssueComment import IssueComment
from gha_issue_resolution.conversation_handler import (
    get_bot_comments,
    get_human_feedback,
    check_triggers
)
from gha_issue_resolution.comment_generator import (
    create_analysis_comment,
    create_response_comment
)

def handle_issue_comment(
    issue: Issue,
    trigger_comment: IssueComment = None
) -> None:
    """Process a GitHub issue comment"""
    # Get any existing bot comments
    bot_comments = get_bot_comments(issue)
    
    # Check if this is a new issue or needs initial analysis
    if not bot_comments:
        print("\nNo existing analysis found, creating initial analysis...")
        create_analysis_comment(issue)
        return
    
    # Get the most recent analysis
    latest_analysis = bot_comments[-1]
    
    # If triggered by a comment, check for triggers
    if trigger_comment:
        create_pr, update_analysis = check_triggers(trigger_comment)
        
        if create_pr:
            print("\nPull request creation triggered...")
            from gha_issue_resolution.pr_handler import create_pr_from_analysis
            create_pr_from_analysis(issue.repository, issue, latest_analysis)
            
        elif update_analysis:
            print("\nUpdated analysis triggered...")
            create_analysis_comment(issue)
            
        else:
            # Respond to the comment
            print("\nGenerating response to comment...")
            create_response_comment(issue, trigger_comment)
