"""Module for handling GitHub issue comments"""
from typing import List
from github.Issue import Issue
from github.IssueComment import IssueComment
from gha_issue_resolution.ai_utils import query_gemini
from gha_issue_resolution.file_utils import get_relevant_files, get_file_content

RESPONSE_TEMPLATE = """## AI-generated response

{response}

To create a pull request with any code changes suggested above, comment with: `/create-pr`
To get an updated analysis, comment with: `/update`"""

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

def create_response_comment(issue: Issue, trigger_comment: IssueComment) -> IssueComment:
    """Generate and post a response to a human comment"""
    print("\nGenerating response to comment...")
    
    # Get conversation history
    conversation = get_conversation_history(issue)
    
    # Get relevant files
    relevant_files = get_relevant_files()
    file_contents = []
    for file_path in relevant_files:
        content = get_file_content(file_path)
        if content and "Error reading file" not in content:
            file_contents.append((file_path, content))
    
    # Create prompt with conversation context
    prompt = f"""Analyze this GitHub issue comment and provide an appropriate response:
    
Issue Title: {issue.title}
Issue Body: {issue.body}

Conversation history:
{'\n'.join(conversation)}

Latest comment to respond to:
{trigger_comment.body}

Please provide:
1. A direct response to the comment
2. If code changes are needed, follow this format:
   
   File: path/to/file.py (CURRENT CONTENT)
   ```python
   # Current content here
   ```
   
   Changes to make:
   - Description of changes needed
   
   File: path/to/file.py (WITH CHANGES)
   ```python
   # Complete new content with changes
   ```
"""
    
    response = query_gemini(prompt, file_contents)
    
    # Format comment using template
    comment_body = RESPONSE_TEMPLATE.format(response=response)
    
    comment = issue.create_comment(comment_body)
    print(f"\nAdded response comment: {comment.html_url}")
    return comment

# Exports
__all__ = ['create_response_comment']