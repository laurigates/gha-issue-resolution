from gha_issue_resolution.comment_handler import create_analysis_comment, get_bot_comments, get_human_feedback
from gha_issue_resolution.pr_handler import create_pr_from_analysis, update_pr_with_feedback

def process_issue(repo, issue):
    """Process a GitHub issue"""
    print(f"\nProcessing issue #{issue.number}: {issue.title}")
    print(f"Issue body: {issue.body}")
    
    # Get any existing bot comments
    bot_comments = get_bot_comments(issue)
    
    # Step 1: Create initial analysis comment if needed
    if not bot_comments:
        print("\nNo existing analysis found, creating initial analysis...")
        analysis_comment = create_analysis_comment(issue)
        bot_comments = [analysis_comment]
    
    # Get the most recent analysis
    latest_analysis = bot_comments[-1]
    
    # Step 2: Get any human feedback
    human_feedback = get_human_feedback(issue, latest_analysis)
    
    # Step 3: Create or update pull request
    try:
        if human_feedback:
            print("\nFound human feedback, updating solution...")
            pr = update_pr_with_feedback(repo, issue, latest_analysis, human_feedback)
        else:
            print("\nCreating pull request from existing analysis...")
            pr = create_pr_from_analysis(repo, issue, latest_analysis)
            
        if pr:
            print(f"Successfully processed issue #{issue.number} with PR #{pr.number}")
        else:
            print(f"No code changes found for issue #{issue.number}")
            
    except Exception as e:
        print(f"Error processing issue #{issue.number}: {str(e)}")
        raise