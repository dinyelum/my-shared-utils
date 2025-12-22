import subprocess
import os


class GitManager:
    def __init__(self, repo=None):
        # if repo==None, current repo is used
        if repo:
            os.chdir(repo)
            print(repo)
            print(f"Current directory: {os.getcwd()}")

    @staticmethod
    def git_add(file_path: str):
        """Stage file for git commit"""
        print(f"Current directory: {os.getcwd()}")
        try:
            subprocess.run(['git', 'add', file_path],
                           check=True, capture_output=True)
            print(f"Git: Staged {file_path}")
        except subprocess.CalledProcessError as e:
            print(f"Git add failed: {e.stderr.decode()}")

    @staticmethod
    def git_commit(message: str):
        """Commit changes to git"""
        try:
            subprocess.run(['git', 'commit', '-m', message],
                           check=True, capture_output=True)
            print(f"Git: Committed with message '{message}'")
        except subprocess.CalledProcessError as e:
            print(f"Git commit failed: {e.stderr.decode()}")

    @staticmethod
    def git_push():
        """Push changes to remote repository"""
        try:
            result = subprocess.run(['git', 'push', 'gh_origin'],
                                    check=True, capture_output=True, text=True)
            print("Git: Successfully pushed to remote repository")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Git push failed: {e.stderr.decode()}")

    @staticmethod
    def git_status():
        """Check git status"""
        try:
            result = subprocess.run(['git', 'status'],
                                    capture_output=True, text=True)
            print("Git Status:")
            print(result.stdout)
        except Exception as e:
            print(f"Git status failed: {e}")
