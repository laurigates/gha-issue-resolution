"""Module for generating GitHub issue comments"""

from typing import List, Tuple
from github.Issue import Issue
from github.IssueComment import IssueComment
from gha_issue_resolution.ai_utils import analyze_issue, query_gemini
from gha_issue_resolution.file_utils import get_repo_structure
from gha_issue_resolution.file_analyzer import get_relevant_files, prepare_file_contents
from gha_issue_resolution.conversation_handler import get_conversation_history
from gha_issue_resolution.comment_types import (
    TRIGGER_PR_COMMENT,
    TRIGGER_UPDATE_COMMENT,
    ANALYSIS_TEMPLATE,
    RESPONSE_TEMPLATE
)

def create_analysis_comment(issue: Issue) -> IssueComment:
    """Generate and post initial analysis comment"""
    print("\nGenerating initial analysis...")
    
    # Get repository structure and find relevant files
    repo_structure = get_repo_structure()
    print("\nGetting repository files...")
    relevant_files = get_relevant_files(repo_structure)
    
    # Get analysis using file API
    analysis_text = analyze_issue(issue, relevant_files)
    
    # Format comment using template
    comment_body = ANALYSIS_TEMPLATE.format(
        analysis=analysis_text,
        pr_trigger=TRIGGER_PR_COMMENT,
        update_trigger=TRIGGER_UPDATE_COMMENT
    )
    
    comment = issue.create_comment(comment_body)
    print(f"\nAdded initial analysis comment: {comment.html_url}")
    return comment

def create_response_comment(
    issue: Issue,
    trigger_comment: IssueComment
) -> IssueComment:
    """Generate and post a response to a human comment"""
    print("\nGenerating response to comment...")
    
    # Get conversation history
    conversation = get_conversation_history(issue)
    
    # Get relevant files and their contents
    repo_structure = get_repo_structure()
    relevant_files = get_relevant_files(repo_structure)
    file_contents = prepare_file_contents(relevant_files)
    
    # Create prompt with conversation context
    prompt = f"""
    Please provide a response to this comment in the context of the GitHub issue:
    
    Issue Title: {issue.title}
    Issue Body: {issue.body}
    
    Previous conversation:
    {'\n'.join(conversation)}
    
    Latest comment to respond to:
    {trigger_comment.body}
    
    Please provide:
    1. A direct response to the comment
    2. If code changes are needed, follow the same format as before:
       
       File: path/to/file.py (CURRENT CONTENT)
       ```python
       # Current content
       ```
       
       Changes to make:
       - Description of changes
       
       File: path/to/file.py (WITH CHANGES)
       ```python
       # New content
       ```
    """
    
    response = query_gemini(prompt, file_contents)
    
    # Format comment using template
    comment_body = RESPONSE_TEMPLATE.format(
        response=response,
        pr_trigger=TRIGGER_PR_COMMENT,
        update_trigger=TRIGGER_UPDATE_COMMENT
    )
    
    comment = issue.create_comment(comment_body)
    print(f"\nAdded response comment: {comment.html_url}")
    return comment
