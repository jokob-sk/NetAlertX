#!/usr/bin/env python3
import json
import re
import subprocess
import sys
import textwrap

# Default Configuration
REPO = "jokob-sk/NetAlertX"
DEFAULT_PR_NUM = "1405"


def get_pr_threads(pr_num):
    """Fetches unresolved review threads using GitHub GraphQL API."""
    # Validate PR number early to avoid passing invalid values to subprocess
    try:
        pr_int = int(pr_num)
        if pr_int <= 0:
            raise ValueError
    except Exception:
        print(f"Error: Invalid PR number: {pr_num}. Must be a positive integer.")
        sys.exit(2)

    query = """
    query($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        pullRequest(number: $number) {
          reviewThreads(last: 100) {
            nodes {
              isResolved
              isOutdated
              comments(first: 1) {
                nodes {
                  body
                  author { login }
                  path
                  line
                }
              }
            }
          }
        }
      }
    }
    """
    owner, name = REPO.split("/")
    cmd = ["gh", "api", "graphql", "-F", f"owner={owner}", "-F", f"name={name}", "-F", f"number={pr_int}", "-f", f"query={query}"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print(f"Error: Command timed out after 60 seconds: {' '.join(cmd)}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR threads: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'gh' CLI not found. Please install GitHub CLI.")
        sys.exit(1)


def clean_block(text):
    """Cleans up markdown/HTML noise from text."""
    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Remove metadata lines
    text = re.sub(r"^\s*Status:\s*\w+", "", text, flags=re.MULTILINE)
    # Remove code block fences
    text = text.replace("```diff", "").replace("```", "")
    # Flatten whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return " ".join(lines)


def extract_ai_tasks(text):
    """Extracts tasks specifically from the 'Fix all issues with AI agents' block."""
    if not text:
        return []

    tasks = []

    # Use case-insensitive search for the AI prompt block
    ai_block_match = re.search(r"(?i)Prompt for AI Agents.*?\n```(.*?)```", text, re.DOTALL)

    if ai_block_match:
        ai_text = ai_block_match.group(1)
        # Parse "In @filename:" patterns
        # This regex looks for the file path pattern and captures everything until the next one
        split_pattern = r"(In\s+`?@[\w\-\./]+`?:)"
        parts = re.split(split_pattern, ai_text)

        if len(parts) > 1:
            for i in range(1, len(parts), 2):
                header = parts[i].strip()
                content = parts[i + 1]
                # Split by bullet points if they exist, or take the whole block
                # Looking for newlines followed by a dash or just the content
                cleaned_sub = clean_block(content)
                if len(cleaned_sub) > 20:
                    tasks.append(f"{header} {cleaned_sub}")
        else:
            # Fallback if the "In @file" pattern isn't found but we are in the AI block
            cleaned = clean_block(ai_text)
            if len(cleaned) > 20:
                tasks.append(cleaned)

    return tasks


def print_task(content, index):
    print(f"\nTask #{index}")
    print("-" * 80)
    print(textwrap.fill(content, width=80))
    print("-" * 80)
    print("1. Plan of action(very brief):")
    print("2. Actions taken (very brief):")
    print("3. quality checks")
    print("- [ ] Issue fully addressed")
    print("- [ ] Unit tests pass")
    print("- [ ] Complete")


def main():
    pr_num = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PR_NUM
    data = get_pr_threads(pr_num)

    threads = data.get("data", {}).get("repository", {}).get("pullRequest", {}).get("reviewThreads", {}).get("nodes", [])

    seen_tasks = set()
    ordered_tasks = []

    for thread in threads:
        # Filter: Unresolved AND Not Outdated
        if thread.get("isResolved") or thread.get("isOutdated"):
            continue

        comments = thread.get("comments", {}).get("nodes", [])
        if not comments:
            continue

        first_comment = comments[0]
        author = first_comment.get("author", {}).get("login", "").lower()

        # Filter: Only CodeRabbit comments
        if author != "coderabbitai":
            continue

        body = first_comment.get("body", "")
        extracted = extract_ai_tasks(body)

        for t in extracted:
            # Deduplicate
            norm_t = re.sub(r"\s+", "", t)[:100]
            if norm_t not in seen_tasks:
                seen_tasks.add(norm_t)
                ordered_tasks.append(t)

    if not ordered_tasks:
        print(f"No unresolved actionable tasks found in PR {pr_num}.")
    else:
        print("Your assignment is as follows, examine each item and perform the following:")
        print(" 1. Create a plan of action")
        print(" 2. Execute your actions")
        print(" 3. Run unit tests to validate")
        print(" 4. After pass, mark complete")
        print("Use the provided fields.\n")
        for i, task in enumerate(ordered_tasks, 1):
            print_task(task, i)


if __name__ == "__main__":
    main()
