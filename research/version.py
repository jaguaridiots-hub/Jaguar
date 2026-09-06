# research/version.py
import subprocess
import os

def get_git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        try:
            with open("VERSION", "r") as f:
                return f.read().strip()
        except:
            return "unknown"

def get_brain_version():
    return os.environ.get("BRAIN_VERSION", "v4")

def get_config_version():
    return os.environ.get("CONFIG_VERSION", "default")

def get_all_versions():
    return {
        "git_commit": get_git_commit(),
        "brain_version": get_brain_version(),
        "config_version": get_config_version()
    }
