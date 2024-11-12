"""Module for managing GitHub issue conversation history"""

from typing import List
from github.Issue import Issue
from github.IssueComment import IssueComment

def get_bot_comments(issue: Issue) -> List[IssueComment]:
    """Get all AI-generated comments on the issue"""
    bot_comments = []
    for comment in issue.get_comments():
        if "AI-generated suggestion" in comment.body or "AI-generated response" in comment.body:
            bot_comments.append(comment)
    return bot_comments

def get_human_feedback(issue: Issue, last_bot_comment: IssueComment) -> List[str]:
    """Get human feedback comments after the last bot comment"""
    all_comments = list(issue.get_comments())
    last_bot_index = all_comments.index(last_bot_comment)
    human_feedback = []
    
    for comment in all_comments[last_bot_index + 1:]:
        if "AI-generated" not in comment.body:
            human_feedback.append(comment.body)
            
    return human_feedback

def get_conversation_history(issue: Issue) -> List[str]:
    """Get formatted conversation history from issue"""
    comments = list(issue.get_comments())
    conversation = []
    
    for comment in comments:
        if comment.user.login == issue.user.login:
            conversation.append(f"User: {comment.body}")
        elif "AI-generated" in comment.body:
            conversation.append(f"Assistant: {comment.body}")
            
    return conversation

def check_triggers(comment: IssueComment) -> tuple[bool, bool]:
    """Check if a comment contains trigger commands"""
    from gha_issue_resolution.comment_types import TRIGGER_PR_COMMENT, TRIGGER_UPDATE_COMMENT
    
    if not comment or not hasattr(comment, 'body'):
        return False, False
    
    body = comment.body.lower()
    return (
        TRIGGER_PR_COMMENT.lower() in body,
        TRIGGER_UPDATE_COMMENT.lower() in body
    )
