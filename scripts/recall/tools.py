import os
import glob
import json
import re
from datetime import datetime
from dateutil import parser as date_parser

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def search_logs(query):
    results = []
    for log_file in glob.glob(os.path.join(LOGS_DIR, '*.json')):
        with open(log_file, encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                continue
            for entry in data:
                if query.lower() in json.dumps(entry).lower():
                    results.append({'file': os.path.basename(log_file), 'entry': entry})
    return results

def search_logs_timewindow(since):
    results = []
    log_files = glob.glob(os.path.join(LOGS_DIR, '*.json'))
    
    for log_file in log_files:
        with open(log_file, encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                continue
            
            for entry in data:
                ts = entry.get('timestamp')
                if ts:
                    try:
                        entry_time = date_parser.parse(ts)
                        if entry_time >= since:
                            results.append({'file': os.path.basename(log_file), 'entry': entry})
                    except Exception:
                        continue
    return results

def read_file(filename):
    try:
        with open(filename, encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[ERROR] Could not read file: {e}"

def search_code(query):
    results = []
    for code_file in glob.glob(os.path.join(CODE_ROOT, '**', '*.py'), recursive=True):
        try:
            with open(code_file, encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if re.search(query, line, re.IGNORECASE):
                        results.append({'file': os.path.relpath(code_file, CODE_ROOT), 'line': i+1, 'content': line.strip()})
        except Exception:
            continue
    return results

def get_current_datetime():
    return {"current_datetime": datetime.now().isoformat()} 