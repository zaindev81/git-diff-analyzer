# git-diff-analyzer

git-diff-analyzer is a CLI tool that uses AI to analyze your Git repository and assist with development workflows.
It helps developers quickly generate branch names, commit messages, and pull request summaries based on code changes.
By automating these repetitive tasks, it improves team productivity and ensures consistent naming and formatting practices.

## 1. Installation & Setup

```sh
# Create and activate a virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv sync

# Create a .env file
cp .env.example .env
```

## 2. Usage

```sh
# Branch Name Suggestions
python main.py branch

# Commit Message Suggestions
python main.py commit

# Using default template
python main.py pr

# Using custom template
python main.py pr pr_template.md
```

## 3. Features

**Branch Name Suggestions:**
- Analyzes diff between current branch and main/master
- Suggests appropriate prefixes (feature/, fix/, refactor/, etc.)
- Provides kebab-case formatted suggestions
- Offers multiple options with the best one first

**PR Summary Generation:**
- Analyzes changes and creates structured summaries
- Supports custom templates
- Includes checklists and organized sections
- Provides technical details for reviewers

**Commit Message Suggestions:**
- Analyzes only staged changes
- Follows Conventional Commits format
- Provides multiple suggestions
- Keeps first line under 50 characters