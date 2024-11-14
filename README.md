# GitHub Issue Resolution with Gemini Flash

An AI-powered GitHub Action that automatically analyzes issues and suggests solutions using Google's Gemini Flash AI model.

## Features

- 🤖 Automated issue analysis
- 💡 AI-generated solution suggestions
- 🔄 Interactive comment-based updates
- 🛠️ Automatic pull request creation
- 📝 Code-aware responses

## Setup

1. Add the action to your repository:

```yaml
name: Issue Resolution

on:
  issues:
    types: [opened]
  issue_comment:
    types: [created]

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  resolve:
    runs-on: ubuntu-latest
    steps:
      - name: Run Issue Resolution
        uses: laurigates/gha-issue-resolution@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
          max-tokens: '8192'
```

2. Add your Gemini API key to repository secrets as `GEMINI_API_KEY`

## Usage

The action automatically responds to:

1. New Issues:
   - Analyzes the issue description
   - Suggests potential solutions
   - Provides code examples when relevant

2. Comments with commands:
   - `/update` - Get an updated analysis
   - `/create-pr` - Create a pull request with suggested changes

## Configuration

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `github-token` | GitHub token for API access | Yes | N/A |
| `gemini-api-key` | Google Gemini API key | Yes | N/A |
| `max-tokens` | Maximum tokens for response | No | 8192 |

## Examples

1. When a new issue is opened:
```
Issue: "Button component not properly handling click events"
↓
AI Response:
- Analyzes the code
- Suggests fixes
- Provides implementation examples
```

2. Using commands in comments:
```
Comment: "/update"
↓
AI Response:
- Fresh analysis of the issue
- Updated solution suggestions
```

```
Comment: "/create-pr"
↓
Result:
- Creates a new branch
- Implements suggested changes
- Opens a pull request
```

## Limitations

- Requires Python 3.12 or higher
- Repository needs appropriate permissions set
- Gemini API access required
- Max token limit applies to responses

## Contributing

Contributions are welcome! Please check out our [Contributing Guidelines](CONTRIBUTING.md).

## License

MIT License - see LICENSE file for details.