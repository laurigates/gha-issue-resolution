from gha_issue_resolution.ai_utils import query_gemini, parse_code_blocks
from gha_issue_resolution.github_utils import create_pull_request

def create_pr_from_analysis(repo, issue, analysis_comment):
    """Create a pull request based on the analysis comment"""
    print("\nExtracting code changes from analysis...")
    
    # Handle both string and comment object
    analysis_text = analysis_comment.body if hasattr(analysis_comment, 'body') else analysis_comment
    code_changes = parse_code_blocks(analysis_text)
    
    if not code_changes:
        print("No code changes found in the analysis")
        return None
    
    print(f"\nFound {len(code_changes)} code changes to implement")
    
    try:
        pr = create_pull_request(repo, issue, analysis_text, code_changes)
        print(f"Created pull request #{pr.number}")
        return pr
    except Exception as e:
        print(f"Error creating pull request: {str(e)}")
        error_comment = f"""
        I encountered an error while trying to create the pull request:
        ```
        {str(e)}
        ```
        Please check the repository permissions and settings.
        """
        issue.create_comment(error_comment)
        raise

def update_pr_with_feedback(repo, issue, analysis_comment, human_feedback):
    """Update solution based on human feedback and create a new PR"""
    if not human_feedback:
        return None
        
    analysis_text = analysis_comment.body if hasattr(analysis_comment, 'body') else analysis_comment
    
    feedback_prompt = f"""
    Please review the previous solution and the human feedback to generate an updated solution.
    
    Previous solution:
    {analysis_text}
    
    Human feedback:
    {'\n'.join(human_feedback)}
    
    Provide an updated solution incorporating the feedback, using the same format with (CURRENT CONTENT) 
    and (WITH CHANGES) markers. Remember to preserve all existing code and only modify what's necessary.
    """
    
    print("\nGenerating updated solution based on feedback...")
    updated_solution = query_gemini(feedback_prompt)
    updated_code_changes = parse_code_blocks(updated_solution)
    
    if updated_code_changes:
        print(f"Using updated solution with {len(updated_code_changes)} code changes")
        return create_pr_from_analysis(repo, issue, updated_solution)
    
    return None