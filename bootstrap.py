import sys
import subprocess
import platform
import os
import shutil
import getpass

# helper to pick the right python path in a venv on Windows vs Unix
def python_in_venv(venv_dir: str) -> str:
    if platform.system() == "Windows":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        return os.path.join(venv_dir, "bin", "python")


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

    # look for any existing venv
    for venv_dir in venv_candidates:
        venv_python = python_in_venv(venv_dir)
        if os.path.exists(venv_python):
            found_venv = venv_dir
            break

    YELLOW = "\033[93m"
    GREEN  = "\033[92m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

    if found_venv:
        print(f"{YELLOW}{BOLD}[INFO] Found existing virtual environment: {found_venv}{RESET}")
        print(f"{YELLOW}Re-running setup.py inside the virtual environment...{RESET}")
        exe = python_in_venv(found_venv)
        os.execv(exe, [exe] + sys.argv)

    # no venv found → create one and re-exec into it
    venv_dir = ".venv"
    print(f"{YELLOW}{BOLD}[INFO] Not running in a virtual environment.{RESET}")
    print(f"{GREEN}Creating a virtual environment at {venv_dir}...{RESET}")
    subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
    print(f"{GREEN}Virtual environment created.{RESET}")
    print(f"{YELLOW}Re-running setup.py inside the virtual environment...{RESET}")
    exe = python_in_venv(venv_dir)
    os.execv(exe, [exe] + sys.argv)

# … rest of your script follows …


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

# 4. Standard setuptools setup
setup(
    name="observer-agent-mvp-recorder",
    version="0.1.0",
    description="Cross-platform screen recording tool for observer-agent-mvp (supports X11, Wayland, Windows, macOS, and OBS Studio)",
    author="Your Name",
    packages=find_packages() + ['scripts', 'scripts.recall'],
    entry_points={
        'console_scripts': [
            'screen-recorder=scripts.recording:main',
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

# Detect if the old console recorder is installed
recorder_path = shutil.which("screen-recorder")

print(f"{GREEN}{BOLD}To launch the desktop UI, run:{RESET} {BOLD}python ui.py{RESET}")
choice = input(f"{GREEN}Launch UI now? (y/N): {RESET}")

if choice.strip().lower() == 'y':
    # Use this venv’s Python to run the new UI
    os.system(f"{sys.executable} ui.py")
else:
    # Fallback to the old recorder script
    if recorder_path:
        print(f"{GREEN}{BOLD}Or start recording directly:{RESET} {BOLD}screen-recorder{RESET}")
    else:
        print(f"{GREEN}{BOLD}Or start recording directly:{RESET} {BOLD}python recording.py{RESET}")