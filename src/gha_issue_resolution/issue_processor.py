import logging
from gha_issue_resolution.github_utils import get_issue

def process_issue(issue_number, repo):
    issue = get_issue(issue_number, repo)
    labels = issue.labels
    if labels is None or len(labels) == 0:
        logging.info(f"Issue #{issue_number} in repo '{repo}' (Title: {issue.title}, URL: {issue.html_url}) has no labels.")
    else:
        # ... existing code that uses issue.labels ...
        for label in labels:
            print(f"Processing label: {label.name}")
        # ... more existing code ...