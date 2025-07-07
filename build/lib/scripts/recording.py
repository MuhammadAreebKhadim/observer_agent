import os
import platform
import shutil
import subprocess
import sys

def is_wayland():
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"

def is_linux():
    return platform.system() == "Linux"

def start_screen_recording(duration_seconds=10):
    if is_linux() and is_wayland():
        # Use wf-recorder if available
        if shutil.which("wf-recorder"):
            RECORDINGS_DIR = "recordings"
            os.makedirs(RECORDINGS_DIR, exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(RECORDINGS_DIR, f"recording_{timestamp}.mp4")
            cmd = [
                "wf-recorder",
                "-f", output_file,
                "-d", str(duration_seconds)
            ]
            print(f"Recording with wf-recorder for {duration_seconds}s to {output_file}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print("[ERROR] wf-recorder failed:")
                print(result.stderr)
                if "wlr-screencopy-unstable-v1" in result.stderr:
                    print("\n[CRITICAL] Your Wayland compositor does not support wlr-screencopy-unstable-v1.\n"
                          "Scriptable screen recording is not possible on this compositor (e.g., GNOME Wayland).\n"
                          "Try switching to an X11 session or a compatible Wayland compositor (like Sway or Hyprland).\n")
                sys.exit(1)
            print(f"Recording saved: {output_file}")
        else:
            print("wf-recorder is not installed or not found in PATH.")
            sys.exit(1)
    else:
        # Use mss for X11, Windows, macOS
        import mss
        import cv2
        import numpy as np
        import time
        from datetime import datetime

        RECORDINGS_DIR = "recordings"
        FPS = 20
        os.makedirs(RECORDINGS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(RECORDINGS_DIR, f"recording_{timestamp}.mp4")
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            width = monitor['width']
            height = monitor['height']
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_file, fourcc, FPS, (width, height))
            print(f"Recording {width}x{height} for {duration_seconds}s to {output_file}")
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                img = np.array(sct.grab(monitor))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                out.write(frame)
                time.sleep(1 / FPS)
            out.release()
            print(f"Recording saved: {output_file}")

def main():
    """Console‐script entry point."""
    start_screen_recording()

if __name__ == "__main__":
    main()