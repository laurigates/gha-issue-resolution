"""Module for handling GitHub issue comments and triggers"""
from typing import List, Tuple
from github.Issue import Issue
from github.IssueComment import IssueComment
from gha_issue_resolution.ai_utils import query_gemini, analyze_issue
from gha_issue_resolution.file_utils import get_relevant_files, get_file_content
from gha_issue_resolution.pr_handler import create_pr_from_analysis

# Command triggers
TRIGGER_PR_COMMENT = "/create-pr"
TRIGGER_UPDATE_COMMENT = "/update"

# Comment templates
ANALYSIS_TEMPLATE = """## AI-generated suggestion

Here's a potential solution to this issue, generated by an AI assistant:

{analysis}

To create a pull request with these changes, comment with: `{pr_trigger}`
To get an updated analysis, comment with: `{update_trigger}`

This is an AI-generated response and requires human validation and testing before implementation."""

RESPONSE_TEMPLATE = """## AI-generated response

{response}

To create a pull request with any code changes suggested above, comment with: `{pr_trigger}`
To get an updated analysis, comment with: `{update_trigger}`"""

def get_bot_comments(issue: Issue) -> List[IssueComment]:
    """Get all AI-generated comments on the issue"""
    bot_comments = []
    for comment in issue.get_comments():
        if "AI-generated suggestion" in comment.body or "AI-generated response" in comment.body:
            bot_comments.append(comment)
    return bot_comments

def get_human_feedback(issue: Issue, after_comment: IssueComment) -> List[str]:
    """Get human feedback comments after a specific comment"""
    all_comments = list(issue.get_comments())
    if after_comment not in all_comments:
        return []
        
    last_bot_index = all_comments.index(after_comment)
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

def create_analysis_comment(issue: Issue) -> IssueComment:
    """Generate and post initial analysis comment"""
    print("\nGenerating initial analysis...")
    
    # Get relevant files
    relevant_files = get_relevant_files()
    print(f"\nAnalyzing {len(relevant_files)} relevant files...")
    
    # Get analysis
    analysis_text = analyze_issue(issue, relevant_files)
    
    # Format comment using template
    comment_body = ANALYSIS_TEMPLATE.format(
        analysis=analysis_text,
        pr_trigger=TRIGGER_PR_COMMENT,
        update_trigger=TRIGGER_UPDATE_COMMENT
    )
    
    comment = issue.create_comment(comment_body)
    print(f"\nAdded analysis comment: {comment.html_url}")
    return comment

def create_response_comment(issue: Issue, trigger_comment: IssueComment) -> IssueComment:
    """Generate and post a response to a human comment"""
    print("\nGenerating response to comment...")
    
    # Get conversation history
    conversation = get_conversation_history(issue)
    
    # Get relevant files
    relevant_files = get_relevant_files()
    file_contents = []
    for file_path in relevant_files:
        if Path(file_path).is_file():
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
    comment_body = RESPONSE_TEMPLATE.format(
        response=response,
        pr_trigger=TRIGGER_PR_COMMENT,
        update_trigger=TRIGGER_UPDATE_COMMENT
    )
    
    comment = issue.create_comment(comment_body)
    print(f"\nAdded response comment: {comment.html_url}")
    return comment

def check_triggers(comment: IssueComment) -> Tuple[bool, bool]:
    """Check if a comment contains trigger commands"""
    if not comment or not hasattr(comment, 'body'):
        return False, False
    
    body = comment.body.strip().lower()
    create_pr = TRIGGER_PR_COMMENT.lower() in body
    update_analysis = TRIGGER_UPDATE_COMMENT.lower() in body
    
    print(f"\nChecking triggers in comment: {body}")
    print(f"Create PR triggered: {create_pr}")
    print(f"Update analysis triggered: {update_analysis}")
    
    return create_pr, update_analysis

def process_comment(repo, issue: Issue, comment: IssueComment) -> None:
    """Process a single comment on an issue"""
    create_pr, update_analysis = check_triggers(comment)
    
    if create_pr or update_analysis:
        print(f"\nProcessing trigger comment on issue #{issue.number}")
        print(f"Comment body: {comment.body}")
        
        # Get existing bot comments
        bot_comments = get_bot_comments(issue)
        latest_analysis = bot_comments[-1] if bot_comments else None
        
        if create_pr and latest_analysis:
            print("\nPull request creation triggered...")
            create_pr_from_analysis(repo, issue, latest_analysis)
        elif update_analysis:
            print("\nUpdated analysis triggered...")
            new_analysis = create_analysis_comment(issue)
            print(f"Created new analysis comment: {new_analysis.html_url}")
        else:
            print("\nGenerating standard response...")
            create_response_comment(issue, comment)
