"""Module for processing GitHub issues and their comments"""
from typing import Optional
from github.Repository import Repository
from github.Issue import Issue
from github.IssueComment import IssueComment
from gha_issue_resolution.comment_handler import (
    get_bot_comments,
    create_analysis_comment,
    process_comment
)

def process_issue(repo: Repository, issue: Issue) -> None:
    """Process a GitHub issue and its comments"""
    print(f"\nProcessing issue #{issue.number}: {issue.title}")
    print(f"Issue body: {issue.body}")
    
    # Get any existing bot comments
    bot_comments = get_bot_comments(issue)
    
    # Get the latest comment that triggered this run
    trigger_comment: Optional[IssueComment] = None
    if hasattr(issue, 'comment'):
        trigger_comment = issue.comment
        print(f"\nTriggered by comment: {trigger_comment.body}")
    
    # Check if this is a new issue or needs initial analysis
    if not bot_comments:
        print("\nNo existing analysis found, creating initial analysis...")
        create_analysis_comment(issue)
        return
    
    # If triggered by a comment, process it
    if trigger_comment:
        print("\nProcessing trigger comment...")
        process_comment(repo, issue, trigger_comment)
