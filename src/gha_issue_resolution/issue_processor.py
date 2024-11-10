from gha_issue_resolution.comment_handler import (
    create_analysis_comment, get_bot_comments, get_human_feedback,
    create_response_comment, check_triggers
)
from gha_issue_resolution.pr_handler import create_pr_from_analysis, update_pr_with_feedback

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
            create_analysis_comment(issue)
        else:
            # Respond to the comment
            print("\nGenerating response to comment...")
            create_response_comment(issue, trigger_comment)