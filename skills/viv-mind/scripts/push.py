#!/usr/bin/env python3
"""Commit, push, and enable GitHub Pages for viv-mind."""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_REPO = Path.home() / ".openclaw" / "workspace" / "viv-mind-scaffold"
DEFAULT_REMOTE = "origin"
DEFAULT_BRANCH = "main"
DEFAULT_OWNER = "vivmuk"
DEFAULT_REPO_NAME = "viv-mind"


def run_git(repo: Path, *args: str, check: bool = True, capture: bool = True) -> str:
    """Run a git command in the repo."""
    cmd = ["git", *args]
    result = subprocess.run(
        cmd,
        cwd=repo,
        capture_output=capture,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def get_github_token() -> str | None:
    """Get GITHUB_TOKEN from env or clawdbot config."""
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return token
    clawdbot = Path.home() / ".clawdbot" / "clawdbot.json"
    if clawdbot.exists():
        try:
            cfg = json.loads(clawdbot.read_text(encoding="utf-8"))
            k = (
                cfg.get("skills", {})
                .get("entries", {})
                .get("viv-mind", {})
                .get("env", {})
                .get("GITHUB_TOKEN", "")
            )
            if k:
                return k.strip()
        except (json.JSONDecodeError, OSError):
            pass
    return None


def require_github_token() -> str:
    token = get_github_token()
    if not token:
        print("Error: GITHUB_TOKEN not set", file=sys.stderr)
        sys.exit(2)
    return token


def gh_api_post(token: str, url: str, payload: dict) -> dict:
    """Make an authenticated GitHub API POST request."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "VivMindSkill/1.0",
        },
        data=body,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error ({e.code}): {error_body}") from e


def ensure_remote(repo: Path, owner: str, repo_name: str, token: str) -> None:
    """Ensure origin points to the target GitHub repo, creating the private repo if needed."""
    https_url = f"https://{token}@github.com/{owner}/{repo_name}.git"
    try:
        remotes = run_git(repo, "remote", "-v")
    except RuntimeError:
        remotes = ""
    if DEFAULT_REMOTE not in remotes:
        run_git(repo, "remote", "add", DEFAULT_REMOTE, https_url)
    else:
        run_git(repo, "remote", "set-url", DEFAULT_REMOTE, https_url)

    # Try to create repo if it doesn't exist (private, no Pages)
    existing = gh_api_get(token, f"https://api.github.com/repos/{owner}/{repo_name}")
    if not existing.get("id"):
        try:
            gh_api_post(
                token,
                "https://api.github.com/user/repos",
                {"name": repo_name, "private": True, "has_pages": False},
            )
            print(f"Created private GitHub repo: {owner}/{repo_name}")
        except RuntimeError as e:
            # org fallback
            if "Not Found" in str(e) or "422" in str(e):
                gh_api_post(
                    token,
                    f"https://api.github.com/orgs/{owner}/repos",
                    {"name": repo_name, "private": True, "has_pages": False},
                )
                print(f"Created private GitHub repo: {owner}/{repo_name}")
            else:
                raise


def gh_api_put(token: str, url: str, payload: dict) -> dict:
    """Make an authenticated GitHub API PUT request."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "VivMindSkill/1.0",
        },
        data=body,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error ({e.code}): {error_body}") from e


def gh_api_get(token: str, url: str) -> dict:
    """Make an authenticated GitHub API GET request."""
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "VivMindSkill/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error ({e.code}): {error_body}") from e


def ensure_repo_private(token: str, owner: str, repo_name: str) -> None:
    """Ensure the repository is private if it already exists."""
    url = f"https://api.github.com/repos/{owner}/{repo_name}"
    req = urllib.request.Request(
        url,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "VivMindSkill/1.0",
        },
        data=json.dumps({"private": True}).encode("utf-8"),
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError:
        pass  # repo may not exist yet


def push(repo: Path, owner: str, repo_name: str, token: str, branch: str, message: str) -> dict:
    """Stage and commit changes if any."""
    run_git(repo, "config", "user.email", "viv-mind@openclaw.local")
    run_git(repo, "config", "user.name", "Viv Mind Bot")
    run_git(repo, "add", "-A")

    status = run_git(repo, "status", "--porcelain")
    if not status.strip():
        return {"committed": False, "message": "No changes to commit"}

    run_git(repo, "commit", "-m", message)
    return {"committed": True, "message": message}


def main() -> int:
    parser = argparse.ArgumentParser(description="Push viv-mind to GitHub.")
    parser.add_argument("--repo", default=str(DEFAULT_REPO), help="Local repo path")
    parser.add_argument("--owner", default=DEFAULT_OWNER, help="GitHub owner")
    parser.add_argument("--name", default=DEFAULT_REPO_NAME, help="GitHub repo name")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="Git branch")
    parser.add_argument("--message", default="Update viv-mind journal", help="Commit message")
    parser.add_argument("--skip-pages", action="store_true", help="Deprecated; GitHub Pages is never enabled")
    parser.add_argument("--private", action="store_true", default=True, help="Ensure repository is private (default: true)")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser()
    token = require_github_token()

    if not (repo / ".git").exists():
        run_git(repo, "init", check=True)

    ensure_remote(repo, args.owner, args.name, token)

    # Ensure the repo is private (best-effort)
    ensure_repo_private(token, args.owner, args.name)

    # Ensure branch exists before pushing
    branches = run_git(repo, "branch", "--list", args.branch, check=False)
    if not branches.strip():
        run_git(repo, "checkout", "-b", args.branch)

    result = push(repo, args.owner, args.name, token, args.branch, args.message)
    print(json.dumps(result, indent=2))

    # Always ensure local branch is pushed, even if no new commit.
    run_git(repo, "push", DEFAULT_REMOTE, args.branch)

    # GitHub Pages intentionally left disabled; Railway hosts the feed.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
