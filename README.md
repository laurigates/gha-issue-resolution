Example workflow

```yaml
name: Issue Resolution

on:
  issues:
    types: [opened, reopened]
  schedule:
    - cron: '0 0 * * *'  # Run daily at midnight
  workflow_dispatch:  # Allow manual triggering

jobs:
  resolve_issues:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Issue Resolution with Gemini
      uses: laurigates/gha-issue-resolution@v1
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
```
