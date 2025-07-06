import os
import sys
import platform
from datetime import datetime
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import SCREENSHOT_WAIT_TIME

# Determine project root and screenshots directory
SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, 'recordings', 'screenshots')
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def is_wayland():
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"

def is_linux():
    return platform.system() == "Linux"

def take_screenshot():
    if SCREENSHOT_WAIT_TIME > 0:
        print(f"[INFO] Waiting {SCREENSHOT_WAIT_TIME} seconds before taking screenshot...")
        time.sleep(SCREENSHOT_WAIT_TIME)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recording_{timestamp}_frame_0.jpg"
    out_path = os.path.join(SCREENSHOTS_DIR, filename)

    if is_linux() and is_wayland():
        # Try to use grim for Wayland screenshots
        if os.system("which grim > /dev/null 2>&1") == 0:
            os.system(f"grim '{out_path}'")
            print(f"[INFO] Screenshot saved to {out_path} (via grim)")
            return out_path
        else:
            print("[ERROR] Wayland detected. Please install 'grim' for screenshots or use X11.")
            return None
    else:
        try:
            import mss
            import cv2
            import numpy as np
        except ImportError:
            print("mss, cv2, and numpy are required. Install with: pip install mss opencv-python numpy")
            return None
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            img = sct.grab(monitor)
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
            cv2.imwrite(out_path, frame)
            print(f"[INFO] Screenshot saved to {out_path} (via mss)")
            return out_path

if __name__ == "__main__":
    take_screenshot() 