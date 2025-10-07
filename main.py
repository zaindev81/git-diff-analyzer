#!/usr/bin/env python3
"""
Git AI Assistant - Suggest branch names, generate PR summaries, and suggest commit messages using OpenAI's API.
"""

import subprocess
import os
import sys
from typing import Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv

base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, '.env')
load_dotenv(dotenv_path)

DEFAULT_MODEL = "gpt-4o-mini"

class GitAIAssistant:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """
        Initialize GitAIAssistant

        Args:
            api_key (str): OpenAI API Key
            model (str): OpenAI model to use
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def run_git_command(self, command: list) -> Tuple[str, str, int]:
        """
        Execute a Git command and return the result

        Args:
            command (list): Git command to execute

        Returns:
            Tuple[str, str, int]: (stdout, stderr, return_code)
        """
        try:
            print(f"Debug: Running command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            print(f"Debug: Return code: {result.returncode}")
            if result.stderr:
                print(f"Debug: Stderr: {result.stderr}")
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            print(f"Debug: Exception: {e}")
            return "", str(e), 1

    def get_current_branch(self) -> Optional[str]:
        """Get the current branch name"""
        stdout, stderr, code = self.run_git_command(["git", "branch", "--show-current"])
        if code == 0:
            branch = stdout.strip()
            print(f"Debug: Current branch: {branch}")
            return branch
        return None

    def get_available_branches(self) -> list:
        """Get list of available branches"""
        stdout, stderr, code = self.run_git_command(["git", "branch", "-a"])
        if code == 0:
            branches = [line.strip().replace('*', '').strip() for line in stdout.split('\n') if line.strip()]
            print(f"Debug: Available branches: {branches}")
            return branches
        return []

    def get_diff_with_main(self) -> Optional[str]:
        """Get diff between current branch and main branch"""
        current_branch = self.get_current_branch()
        if not current_branch:
            print("Debug: Could not determine current branch")
            return None

        print(f"Debug: Current branch is: {current_branch}")

        # Check if we're on main/master already
        if current_branch in ['main', 'master']:
            print("Debug: Currently on main/master branch, checking for uncommitted changes")
            # Get uncommitted changes
            stdout, stderr, code = self.run_git_command(["git", "diff"])
            if code == 0 and stdout.strip():
                print(f"Debug: Found uncommitted changes ({len(stdout)} characters)")
                return stdout
            else:
                print("Debug: No uncommitted changes found")
                return None

        # Try different base branches
        base_branches = ['main', 'master', 'origin/main', 'origin/master']

        for base in base_branches:
            print(f"Debug: Trying diff with {base}")
            stdout, stderr, code = self.run_git_command(["git", "diff", base])
            if code == 0:
                if stdout.strip():
                    print(f"Debug: Found diff with {base} ({len(stdout)} characters)")
                    return stdout
                else:
                    print(f"Debug: No diff with {base}")
            else:
                print(f"Debug: Failed to diff with {base}: {stderr}")

        # If no base branch found, try HEAD~1
        print("Debug: Trying diff with HEAD~1")
        stdout, stderr, code = self.run_git_command(["git", "diff", "HEAD~1"])
        if code == 0 and stdout.strip():
            print(f"Debug: Found diff with HEAD~1 ({len(stdout)} characters)")
            return stdout

        print("Debug: No diff found with any method")
        return None

    def get_diff_for_branch_naming(self) -> Optional[str]:
        """
        Get diff for branch name suggestions
        For main/master branches, also check staged changes
        """
        current_branch = self.get_current_branch()
        if not current_branch:
            print("Debug: Could not determine current branch")
            return None

        print(f"Debug: Getting diff for branch naming, current branch: {current_branch}")

        # If on main/master, first try to get diff with main, then staged changes
        if current_branch in ['main', 'master']:
            print("Debug: On main/master branch, checking uncommitted changes first")
            # Get uncommitted changes
            stdout, stderr, code = self.run_git_command(["git", "diff"])
            if code == 0 and stdout.strip():
                print(f"Debug: Found uncommitted changes ({len(stdout)} characters)")
                return stdout

            # If no uncommitted changes, try staged changes
            print("Debug: No uncommitted changes, checking staged changes")
            staged_diff = self.get_staged_diff()
            if staged_diff:
                print(f"Debug: Found staged changes for branch naming ({len(staged_diff)} characters)")
                return staged_diff

            print("Debug: No uncommitted or staged changes found")
            return None

        # For other branches, use the regular diff with main
        return self.get_diff_with_main()

    def get_staged_diff(self) -> Optional[str]:
        """Get diff of staged changes"""
        stdout, stderr, code = self.run_git_command(["git", "diff", "--staged"])
        if code == 0 and stdout.strip():
            print(f"Debug: Found staged changes ({len(stdout)} characters)")
            return stdout
        print("Debug: No staged changes found")
        return None

    def get_git_status(self) -> str:
        """Get git status for debugging"""
        stdout, stderr, code = self.run_git_command(["git", "status", "--porcelain"])
        if code == 0:
            return stdout
        return ""

    def suggest_branch_name(self, diff_content: str) -> str:
        """
        Suggest branch names based on diff content

        Args:
            diff_content (str): Git diff content

        Returns:
            str: Suggested branch names
        """
        if not diff_content or len(diff_content.strip()) < 10:
            return "Error: Diff content is too short or empty to analyze."

        prompt = f"""
Analyze the following Git diff and suggest appropriate branch names.

Rules:
- Use kebab-case (hyphen-separated)
- Keep names concise and descriptive
- Properly represent the changes made
- Follow common Git branch naming conventions
- Use appropriate prefixes like feature/, fix/, refactor/, docs/, etc.

Git diff:
```
{diff_content[:2000]}...
```

Please suggest 3 branch names. List the most appropriate one first.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Git expert. Analyze code changes and suggest appropriate branch names."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            result = response.choices[0].message.content.strip()
            result = result.replace("**", "")
            result = result.replace("*", "")
            result = result.replace("`", "")

            return result
        except Exception as e:
            return f"An error occurred: {e}"

    def generate_pr_summary(self, diff_content: str, template: str = None) -> str:
        """
        Generate PR summary based on diff content

        Args:
            diff_content (str): Git diff content
            template (str): Template to use

        Returns:
            str: PR summary
        """
        if not diff_content or len(diff_content.strip()) < 10:
            return "Error: Diff content is too short or empty to analyze."

        if template is None:
            template = """
## Summary
[Brief description of changes]

## Changes Made
- [Change 1]
- [Change 2]
- [Change 3]

## Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Checklist
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Tests added/updated
"""

        prompt = f"""
Analyze the following Git diff and generate a GitHub Pull Request summary.

Template:
{template}

Git diff:
```
{diff_content[:3000]}...
```

Follow the template above and analyze the changes to create an appropriate PR summary.
Include technical details to help reviewers understand the changes.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a software development expert. Analyze Git diffs and create appropriate Pull Request summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"An error occurred: {e}"


    def suggest_commit_message(self, diff_content: str) -> str:
        """
        Suggest commit messages based on staged changes

        Args:
            diff_content (str): Git diff content

        Returns:
            str: Suggested commit messages
        """
        if not diff_content or len(diff_content.strip()) < 10:
            return "Error: Diff content is too short or empty to analyze."

        prompt = f"""
Analyze the following Git diff and suggest appropriate commit messages.

Rules:
- Use Conventional Commits format (type: description)
- Keep the first line under 50 characters
- Add detailed description after blank line if necessary
- Write in English
- Type examples: feat, fix, docs, style, refactor, test, chore

Git diff:
```
{diff_content[:2000]}...
```

Please suggest 3 commit messages. List the most appropriate one first.
    """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Git expert. Analyze changes and suggest appropriate commit messages."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400
            )

            result = response.choices[0].message.content.strip()
            result = result.replace("**", "")
            result = result.replace("*", "")

            return result
        except Exception as e:
            return f"An error occurred: {e}"

def main():
    """Main function"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: Please set the OPENAI_API_KEY environment variable.")
        sys.exit(1)

    assistant = GitAIAssistant(api_key)

    if len(sys.argv) < 2:
        print("""
Usage:
  python main.py branch    - Suggest branch names
  python main.py pr        - Generate PR summary
  python main.py commit    - Suggest commit messages
  python main.py debug     - Show debug information
        """)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "debug":
        print("Debug Information:")
        print("=" * 60)
        print(f"Current working directory: {os.getcwd()}")

        # Check if we're in a git repo
        stdout, stderr, code = assistant.run_git_command(["git", "rev-parse", "--is-inside-work-tree"])
        if code != 0:
            print("Error: Not in a Git repository")
            sys.exit(1)

        # Show current branch
        current_branch = assistant.get_current_branch()
        print(f"Current branch: {current_branch}")

        # Show available branches
        branches = assistant.get_available_branches()
        print(f"Available branches: {branches}")

        # Show git status
        status = assistant.get_git_status()
        print(f"Git status:\n{status}")

        # Try to get diff
        diff = assistant.get_diff_with_main()
        if diff:
            print(f"Diff found: {len(diff)} characters")
            print("First 200 characters of diff:")
            print(diff[:200])
        else:
            print("No diff found")

        # Also try staged diff
        staged_diff = assistant.get_staged_diff()
        if staged_diff:
            print(f"Staged diff found: {len(staged_diff)} characters")
            print("First 200 characters of staged diff:")
            print(staged_diff[:200])
        else:
            print("No staged diff found")

        return

    elif command == "branch":
        print("Suggesting branch names...")
        diff = assistant.get_diff_for_branch_naming()
        if not diff:
            print("No diff found. Possible reasons:")
            print("1. You're on main/master with no uncommitted or staged changes")
            print("2. No differences between current branch and main/master")
            print("3. Main/master branch doesn't exist")
            print("\nTip: If you have changes to commit, try 'git add' to stage them first")
            print("Try running: python main.py debug")
            sys.exit(1)

        suggestion = assistant.suggest_branch_name(diff)
        print("=" * 60)
        print("Suggested Branch Names:")
        print("=" * 60)
        print(suggestion)

    elif command == "pr":
        print("Generating PR summary...")
        diff = assistant.get_diff_with_main()
        if not diff:
            print("No diff found with main branch.")
            print("Try running: python main.py debug")
            sys.exit(1)

        custom_template = None
        if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
            with open(sys.argv[2], 'r', encoding='utf-8') as f:
                custom_template = f.read()

        summary = assistant.generate_pr_summary(diff, custom_template)
        print("=" * 60)
        print("PR Summary:")
        print("=" * 60)
        print(summary)

    elif command == "commit":
        print("Suggesting commit messages...")
        diff = assistant.get_staged_diff()
        if not diff:
            print("No staged changes found.")
            print("Please stage files with 'git add' before running this command.")
            print("Or try running: python main.py debug")
            sys.exit(1)

        suggestion = assistant.suggest_commit_message(diff)
        print("=" * 60)
        print("Suggested Commit Messages:")
        print("=" * 60)
        print(suggestion)

    else:
        print(f"Unknown command: {command}")
        print("Available commands: branch, pr, commit, debug")
        sys.exit(1)

if __name__ == "__main__":
    main()
