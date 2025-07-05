import sys
import subprocess
import platform
import os
import shutil
import getpass

# --- VENV CHECK AND AUTO-REEXECUTION (with multiple candidates) ---
def in_venv():
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )

# List of possible venv folder names (in order of preference)
venv_candidates = [".venv", "venv", "env", "ENV", ".env"]

if not in_venv():
    found_venv = None
    for venv_dir in venv_candidates:
        venv_python = os.path.join(venv_dir, "bin", "python")
        if os.path.exists(venv_python):
            found_venv = venv_dir
            break
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    if found_venv:
        print(f"{YELLOW}{BOLD}[INFO] Found existing virtual environment: {found_venv}{RESET}")
        print(f"{YELLOW}Re-running setup.py inside the virtual environment...{RESET}")
        os.execv(os.path.join(found_venv, "bin", "python"), [os.path.join(found_venv, "bin", "python")] + sys.argv)
    else:
        venv_dir = ".venv"
        print(f"{YELLOW}{BOLD}[INFO] Not running in a virtual environment.{RESET}")
        print(f"{GREEN}Creating a virtual environment at {venv_dir}...{RESET}")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
        print(f"{GREEN}Virtual environment created.{RESET}")
        print(f"{YELLOW}Re-running setup.py inside the virtual environment...{RESET}")
        os.execv(os.path.join(venv_dir, "bin", "python"), [os.path.join(venv_dir, "bin", "python")] + sys.argv)

def run(cmd, check=True, input_text=None):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, input=input_text, text=True)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result

# 1. Ensure setuptools is installed
try:
    import setuptools
except ImportError:
    print("[INFO] setuptools not found. Installing setuptools...")
    run([sys.executable, "-m", "pip", "install", "setuptools"])

from setuptools import setup, find_packages

# 2. Install Python dependencies
# NEW: Install from requirements.txt
try:
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
except Exception as e:
    print("[ERROR] Failed to install Python dependencies from requirements.txt:", e)
    sys.exit(1)

# 3. Install system dependency if on Wayland + Linux + apt
if platform.system() == "Linux" and os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if "gnome" in desktop:
        YELLOW = "\033[93m"
        GREEN = "\033[92m"
        BOLD = "\033[1m"
        RESET = "\033[0m"
        print(f"""
{YELLOW}{BOLD}==================== GNOME Wayland Detected ===================={RESET}
{BOLD}Scriptable screen recording is {YELLOW}NOT possible{RESET}{BOLD} on this setup.{RESET}

{GREEN}To enable screen recording:{RESET}
  1. Save your work and log out of your desktop session.
  2. At the login screen, click your username.
  3. {BOLD}Before entering your password, click the gear icon (⚙️) and select 'GNOME on Xorg' or 'Ubuntu on Xorg'.{RESET}
  4. Log in as usual.
  5. Open a terminal and run: {BOLD}echo $XDG_SESSION_TYPE{RESET}
     It should say: {GREEN}x11{RESET}
  6. Now you can run your screen recording script!

If you do not see the gear icon, let your system administrator know or consult your distribution's documentation.
{YELLOW}{BOLD}===============================================================
{RESET}""")
    if shutil.which("apt"):
        if shutil.which("wf-recorder") is None:
            print("\n[INFO] wf-recorder is required for screen recording on some Wayland compositors.")
            password = getpass.getpass("Enter your sudo password to install wf-recorder: ")
            try:
                result = run(["sudo", "-S", "apt", "install", "-y", "wf-recorder"], input_text=password + "\n")
                print(result.stdout if hasattr(result, 'stdout') else "")
                print("[INFO] wf-recorder installed successfully.")
            except Exception as e:
                print("[WARNING] Could not install wf-recorder automatically. Please install it manually.")
                print(str(e))
    else:
        print("\n[WARNING] Could not find apt. Please install wf-recorder manually for your distribution.")

# --- GIT PRE-PUSH HOOK SETUP ---
def setup_pre_push_hook():
    hooks_dir = os.path.join(os.getcwd(), ".git", "hooks")
    pre_push_path = os.path.join(hooks_dir, "pre-push")
    hook_content = '''#!/bin/sh

# Pre-push hook to prevent pushing from main or master branch

current_branch=$(git symbolic-ref --short HEAD 2>/dev/null)

if [ "$current_branch" = "main" ] || [ "$current_branch" = "master" ]; then
    echo "❌ ERROR: Pushing from $current_branch branch is not allowed!"
    echo "Please create a feature branch and push from there instead."
    exit 1
fi

exit 0
'''
    if not os.path.exists(pre_push_path):
        try:
            os.makedirs(hooks_dir, exist_ok=True)
            with open(pre_push_path, "w") as f:
                f.write(hook_content)
            os.chmod(pre_push_path, 0o755)
            print("[INFO] Git pre-push hook created to block pushes from main/master branch.")
        except Exception as e:
            print(f"[WARNING] Could not create pre-push hook: {e}")
    else:
        print("[INFO] Git pre-push hook already exists.")

# Call the setup function early in the script
setup_pre_push_hook()

# 4. Standard setuptools setup
setup(
    name="observer-agent-mvp-recorder",
    version="0.1.0",
    description="Cross-platform screen recording tool for observer-agent-mvp (supports X11, Wayland, Windows, macOS, and OBS Studio)",
    author="Your Name",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'screen-recorder=recording:main',
        ],
    },
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    long_description="""
A simple, robust, cross-platform screen recording tool for Python. 
- Uses mss and opencv-python for Windows, macOS, and X11 Linux.
- Uses wf-recorder (system dependency) for some Wayland compositors.
- Uses OBS Studio + obs-websocket for universal, scriptable recording on all platforms (including GNOME Wayland).
    """,
    long_description_content_type="text/markdown",
)

print("\n[ALL DONE] Your environment is ready!")
print("\n[INFO] For universal screen recording (including GNOME Wayland), please:")
print("  1. Install OBS Studio from https://obsproject.com/")
print("  2. Enable obs-websocket (built-in for OBS 28+; see https://github.com/obsproject/obs-websocket)")
print("  3. Configure OBS to capture your screen and set up the WebSocket server.")
print("  4. Use the provided Python script to automate recording via obs-websocket-py.")
print("\nSee README for details and example scripts.\n")

GREEN = "\033[92m"
BOLD = "\033[1m"
RESET = "\033[0m"

recorder_path = shutil.which("screen-recorder")
if recorder_path:
    print(f"{GREEN}{BOLD}To start recording, run:{RESET} {BOLD}screen-recorder{RESET}")
    user_input = input(f"{GREEN}Would you like to run the screen recorder now? (y/N): {RESET}")
    if user_input.strip().lower() == 'y':
        print(f"{GREEN}Starting screen recorder...{RESET}")
        os.system("screen-recorder")
else:
    print(f"{GREEN}{BOLD}To start recording, run:{RESET} {BOLD}python recording.py{RESET}")
    user_input = input(f"{GREEN}Would you like to run the screen recorder now? (y/N): {RESET}")
    if user_input.strip().lower() == 'y':
        print(f"{GREEN}Starting screen recorder...{RESET}")
        os.system(f"{sys.executable} recording.py") 