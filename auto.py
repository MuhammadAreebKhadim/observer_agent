import os
import subprocess
import glob
import time
import argparse
import json
from datetime import datetime
from config import CAPTURE_MODE, AUTO_LOOP_DELAY


def print_latest_log():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(base_dir, 'logs')
    log_files = glob.glob(os.path.join(logs_dir, '*.json'))
    if not log_files:
        print('[INFO] No log files found.')
        return
    latest_log = max(log_files, key=os.path.getctime)
    print(f'[INFO] Showing latest log: {latest_log}')
    with open(latest_log, 'r') as f:
        print(f.read())


def run_workflow(session_log_path=None, session_id=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(base_dir, 'scripts')
    screenshots_dir = os.path.join(base_dir, 'recordings', 'screenshots')

    if CAPTURE_MODE == 'screenshot':
        # Run screenshot_take.py
        script_path = os.path.join(scripts_dir, 'screenshot_take.py')
        if os.path.exists(script_path):
            print(f"Running screenshot_take.py")
            subprocess.run(['python3', script_path])
        else:
            print(f"Script not found: {script_path}")
        # Find the latest screenshot
        screenshot_files = glob.glob(os.path.join(screenshots_dir, '*.jpg'))
        if screenshot_files:
            latest_screenshot = max(screenshot_files, key=os.path.getctime)
            print(f"Latest screenshot: {latest_screenshot}")
            # Run summarize_and_insert_logs.py with the screenshot path and session log path
            script_path = os.path.join(scripts_dir, 'summarize_and_insert_logs.py')
            if os.path.exists(script_path):
                cmd = ['python3', script_path, latest_screenshot]
                if session_log_path:
                    cmd.append(session_log_path)
                if session_id:
                    cmd.append(session_id)
                print(f"Running summarize_and_insert_logs.py {cmd[2:]}")
                subprocess.run(cmd)
            else:
                print(f"Script not found: {script_path}")
        else:
            print("No screenshots found to summarize.")
    else:
        # 1. Run recording.py
        script_path = os.path.join(scripts_dir, 'recording.py')
        if os.path.exists(script_path):
            print(f"Running recording.py")
            subprocess.run(['python3', script_path])
        else:
            print(f"Script not found: {script_path}")

        # 2. Run extract_multiple_frames.py
        script_path = os.path.join(scripts_dir, 'extract_multiple_frames.py')
        if os.path.exists(script_path):
            print(f"Running extract_multiple_frames.py")
            subprocess.run(['python3', script_path])
        else:
            print(f"Script not found: {script_path}")

        # 3. Find the latest screenshot
        screenshot_files = glob.glob(os.path.join(screenshots_dir, '*.jpg'))
        if screenshot_files:
            latest_screenshot = max(screenshot_files, key=os.path.getctime)
            print(f"Latest screenshot: {latest_screenshot}")
            # 4. Run summarize_and_insert_logs.py with the screenshot path and session log path
            script_path = os.path.join(scripts_dir, 'summarize_and_insert_logs.py')
            if os.path.exists(script_path):
                cmd = ['python3', script_path, latest_screenshot]
                if session_log_path:
                    cmd.append(session_log_path)
                if session_id:
                    cmd.append(session_id)
                print(f"Running summarize_and_insert_logs.py {cmd[2:]}")
                subprocess.run(cmd)
            else:
                print(f"Script not found: {script_path}")
        else:
            print("No screenshots found to summarize.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated screen capture and logging.")
    parser.add_argument('--continually', action='store_true', help='Run the workflow in a loop with delay between runs')
    args = parser.parse_args()

    session_log_path = None
    session_id = None
    if args.continually:
        # Generate a session log filename and session_id
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_dir, 'logs')
        session_id = datetime.now().strftime('session_%Y%m%d_%H%M%S')
        session_log_path = os.path.join(logs_dir, f'{session_id}.json')
        print(f"[INFO] Session log file: {session_log_path}")

    if args.continually:
        print(f"[INFO] Running in continual mode. Delay between runs: {AUTO_LOOP_DELAY} seconds.")
        while True:
            run_workflow(session_log_path=session_log_path, session_id=session_id)
            print(f"[INFO] Waiting {AUTO_LOOP_DELAY} seconds before next run...")
            time.sleep(AUTO_LOOP_DELAY)
    else:
        run_workflow() 