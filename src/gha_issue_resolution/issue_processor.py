from pathlib import Path
import traceback
from gha_issue_resolution.github_utils import create_pull_request, get_bot_comments
from gha_issue_resolution.ai_utils import query_gemini, parse_code_blocks, generate_detailed_prompt
from gha_issue_resolution.file_utils import get_repo_structure, get_file_content

def process_issue(issue):
    print(f"\nProcessing issue #{issue.number}: {issue.title}")
    print(f"Issue body: {issue.body}")
    
    # Get any existing bot comments
    bot_comments = get_bot_comments(issue)
    
    # Check if issue needs analysis comment
    needs_analysis = not bot_comments
    
    if needs_analysis:
        print("\nGenerating initial analysis...")
        # Generate and post initial analysis
        repo_structure = get_repo_structure()
        initial_prompt = f"""
        Analyze this GitHub issue and suggest a solution based on the repository structure:
        
        Issue Title: {issue.title}
        Issue Body: {issue.body}
        
        Repository Structure:
        {repo_structure}
        
        Provide:
        1. A brief analysis of the issue.
        2. A list of files that are likely relevant to this issue (up to 5 files).
        3. An initial approach for solving this issue.
        """
        
        initial_response = query_gemini(initial_prompt)
        
        # Extract file paths from the initial response
        file_paths = [line.split()[-1] for line in initial_response.split('\n') if line.startswith('-') and '.' in line]
        print(f"\nIdentified relevant files: {file_paths}")
        
        # Use the new prompt generator
        detailed_prompt = generate_detailed_prompt(issue, initial_response, file_paths)

        print("\nGenerating detailed solution...")
        detailed_solution = query_gemini(detailed_prompt)
        
        comment_body = f"""
        ## AI-generated suggestion

        Here's a potential solution to this issue, generated by an AI assistant:

        {detailed_solution}

        I can create a pull request with these suggested changes. Please review the suggestion and add any additional comments or requirements.
        This is an AI-generated response and requires human validation and testing before implementation.
        """
        
        comment = issue.create_comment(comment_body)
        print(f"\nAdded initial analysis comment: {comment.html_url}")
        bot_comments = [comment]  # Update bot_comments with the new comment
    
    # Get the most recent bot comment
    latest_bot_comment = bot_comments[-1]
    
    # Look for additional human comments after the last bot comment
    all_comments = list(issue.get_comments())
    last_bot_index = all_comments.index(latest_bot_comment)
    human_feedback = []
    for comment in all_comments[last_bot_index + 1:]:
        if "AI-generated suggestion" not in comment.body:
            human_feedback.append(comment.body)
    
    # Generate pull request if there's a solution in the bot comments
    print("\nExtracting code changes from previous analysis...")
    code_changes = parse_code_blocks(latest_bot_comment.body)
    
    if code_changes:
        print(f"\nFound {len(code_changes)} code changes to implement")
        
        if human_feedback:
            # If there's human feedback, generate an updated solution
            feedback_prompt = f"""
            Please review the previous solution and the human feedback to generate an updated solution.
            
            Previous solution:
            {latest_bot_comment.body}
            
            Human feedback:
            {'\n'.join(human_feedback)}
            
            Provide an updated solution incorporating the feedback, using the same format with (CURRENT CONTENT) 
            and (WITH CHANGES) markers. Remember to preserve all existing code and only modify what's necessary.
            """
            
            print("\nGenerating updated solution based on feedback...")
            updated_solution = query_gemini(feedback_prompt)
            updated_code_changes = parse_code_blocks(updated_solution)
            
            if updated_code_changes:
                code_changes = updated_code_changes
                print(f"Using updated solution with {len(code_changes)} code changes")
        
        try:
            pr = create_pull_request(repo, issue, latest_bot_comment.body, code_changes)
            print(f"Created pull request #{pr.number}")
        except Exception as e:
            print(f"Error creating pull request: {str(e)}")
            print(traceback.format_exc())
            issue.create_comment(f"""
            I encountered an error while trying to create the pull request:
            ```
            {str(e)}
            ```
            Please check the repository permissions and settings.
            """)
    else:
        print("\nNo code changes found in the solution")