import json

def process_issue(issue_data):
    try:
        labels = issue_data['labels']
        # ... your existing code that uses labels.  For example:
        for label in labels:
            if label['name'] == "bug":
                # Do something specific for bug labels
                print(f"Issue #{issue_data['number']} is a bug.")
            elif label['name'] == "enhancement":
                # Do something else
                print(f"Issue #{issue_data['number']} is an enhancement.")

    except KeyError:
        print(f"Warning: Issue #{issue_data['number']} does not have labels. Skipping label-dependent actions.")
        # Optional: Log the issue ID for later review.  Consider adding it to a file or a dedicated log system.
        # with open('issues_without_labels.log', 'a') as f:
        #     f.write(f"Issue {issue_data['number']} has no labels\n")

    except Exception as e: # Catch other potential errors during label processing
        print(f"Error processing issue #{issue_data['number']}: {e}")

# Example usage (assuming you fetch issue data as a JSON string)
issue_json_string =  # ... your code to fetch issue data from GitHub API ...
issue_json = json.loads(issue_json_string)
process_issue(issue_json)
