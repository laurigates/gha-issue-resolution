# GitHub Issue Resolution with Gemini Flash

A GitHub Action that leverages Google's Gemini Flash model to automatically analyze GitHub issues and provide AI-powered solution suggestions. The action processes issues as they are created or updated, delivering detailed code analysis and specific recommendations for fixes.

## Key Features

- 🚀 **Fast Analysis**: Uses Google's Gemini Flash model for rapid issue processing
- 💡 **Intelligent Solutions**: Provides context-aware code suggestions based on your repository
- 🔄 **Interactive Workflow**: Supports both automatic and manual trigger commands
- 🔍 **Deep Code Understanding**: Analyzes repository structure and relevant files
- 🛠️ **Automated PR Creation**: Can create pull requests with suggested changes
- 🔒 **Safety First**: Implements comprehensive safety filters and code validation
- 📝 **Detailed Documentation**: Provides clear explanations for all suggested changes

## Setup

1. Create a workflow file (e.g., `.github/workflows/issue-analysis.yml`):

```yaml
name: Analyze Issues
on:
  issues:
    types: [opened, reopened, edited]
  issue_comment:
    types: [created]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: laurigates/gha-issue-resolution@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
```

2. Configure GitHub repository secrets:
   - `GEMINI_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - `GITHUB_TOKEN`: Automatically provided by GitHub Actions

## Usage

### Automatic Analysis

The action automatically runs when:
- A new issue is created
- An existing issue is reopened
- An issue is edited

### Manual Commands

Comment on any issue with:
- `/create-pr`: Create a pull request with the suggested changes
- `/update`: Get an updated analysis of the issue

### Advanced Configuration

Customize the action with optional inputs:

```yaml
steps:
  - uses: laurigates/gha-issue-resolution@main
    with:
      github_token: ${{ secrets.GITHUB_TOKEN }}
      gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
      max_tokens: '16384'  # Customize response length (default: 8192)
```

## How It Works

1. **Issue Analysis**:
   - Examines issue title and description
   - Scans repository structure
   - Identifies relevant code files
   - Analyzes code context

2. **Solution Generation**:
   - Generates detailed problem analysis
   - Identifies affected files
   - Creates specific code suggestions
   - Explains implementation details
   - Notes potential side effects

3. **Response Format**:
   ```markdown
   ## AI-generated suggestion

   Analysis of the problem...

   File: path/to/file.py (CURRENT CONTENT)
   ```python
   # Current code
   ```

   Changes to make:
   - Change description 1
   - Change description 2

   File: path/to/file.py (WITH CHANGES)
   ```python
   # Updated code
   ```
   ```

4. **Pull Request Creation**:
   - Creates a new branch
   - Implements suggested changes
   - Opens a pull request
   - Links PR to original issue

## Technical Details

### Requirements

- Python 3.12 or higher
- Dependencies:
  - `PyGithub>=1.55`
  - `google-generativeai>=0.8.3`

### Limitations

- Maximum file size: 100,000 characters per file
- Response token limit: 8,192 (configurable)
- Supported file types:
  - Python (.py)
  - JavaScript (.js, .jsx)
  - TypeScript (.ts, .tsx)
  - HTML/CSS
  - YAML/JSON
  - Markdown
  - Text files

## Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/laurigates/gha-issue-resolution.git
   cd gha-issue-resolution
   ```

2. Install dependencies:
   ```bash
   pip install pdm
   pdm install
   ```

3. Set environment variables:
   ```bash
   export GITHUB_TOKEN='your_token'
   export GEMINI_API_KEY='your_key'
   export GITHUB_REPOSITORY='owner/repo'
   ```

4. Run locally:
   ```bash
   pdm run start
   ```

## Project Structure

```
.
├── action.yml              # Action definition
├── pyproject.toml         # Project configuration
├── src/
│   └── gha_issue_resolution/
│       ├── __init__.py
│       ├── __main__.py    # Entry point
│       ├── ai_utils.py    # Gemini API integration
│       ├── comment_handler.py  # Issue comment processing
│       ├── file_utils.py  # File operations
│       ├── github_utils.py    # GitHub API integration
│       ├── issue_processor.py # Main issue logic
│       └── pr_handler.py  # Pull request creation
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- **Issues**: Use [GitHub Issues](https://github.com/laurigates/gha-issue-resolution/issues) for bugs and feature requests
- **Discussions**: Start a discussion for questions and help

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
