"""
Push local Bloomberg repository to GitHub (https://github.com/netflix2023/bloomberg-comp.git)
Uses dulwich pure-Python Git client.
"""

import sys
import os
import getpass
from dulwich.repo import Repo
from dulwich import porcelain

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
REMOTE_URL = "https://github.com/netflix2023/bloomberg-comp.git"

def main():
    print(f"Opening repository at {REPO_DIR}...")
    repo = Repo(REPO_DIR)
    
    # Check if remote exists
    config = repo.get_config()
    config.set(('remote', 'origin'), 'url', REMOTE_URL.encode())
    config.write_to_path()
    print(f"Remote 'origin' set to: {REMOTE_URL}")

    token = os.environ.get("GITHUB_TOKEN")
    if not token and len(sys.argv) > 1:
        token = sys.argv[1]
    
    if not token:
        print("\nGitHub authentication required to push over HTTPS.")
        print("Please provide your GitHub Personal Access Token (PAT):")
        print("Tip: You can generate one at https://github.com/settings/tokens (with 'repo' scope)")
        try:
            token = input("GitHub PAT: ").strip()
        except EOFError:
            print("No input provided. Set GITHUB_TOKEN environment variable or pass token as argument:")
            print("  python push_to_github.py <YOUR_GITHUB_TOKEN>")
            return

    if not token:
        print("Error: No token provided.")
        return

    # Authenticated push URL
    # https://<TOKEN>@github.com/netflix2023/bloomberg-comp.git
    auth_url = f"https://{token}@github.com/netflix2023/bloomberg-comp.git"
    print("Pushing branch 'main' to GitHub remote...")
    try:
        porcelain.push(repo, auth_url, refspecs=[b"refs/heads/main:refs/heads/main"])
        print("Successfully pushed to https://github.com/netflix2023/bloomberg-comp.git!")
    except Exception as e:
        print(f"Push failed: {e}")

if __name__ == "__main__":
    main()
