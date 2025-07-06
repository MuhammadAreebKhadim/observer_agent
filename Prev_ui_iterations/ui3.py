# ui.py
import os
import sys
import threading
import glob
import PySimpleGUI as sg

from scripts.recording import start_screen_recording
from scripts.recall.__main__ import main as run_recall

# ---------------------
# Helper threads
# ---------------------
def threaded_record(window, seconds):
    window.write_event_value('-REC-OUT-', ("info", f"Recording for {seconds}s…"))
    try:
        start_screen_recording(duration_seconds=seconds)
        window.write_event_value('-REC-OUT-', ("success", f"Done: {seconds}s saved in recordings/"))
    except Exception as e:
        window.write_event_value('-REC-OUT-', ("error", f"Recording error: {e}"))

def threaded_recall(window):
    window.write_event_value('-RECALL-OUT-', ("info", "Running recall…"))
    try:
        run_recall()
        window.write_event_value('-RECALL-OUT-', ("success", "Recall complete. See logs/"))
    except Exception as e:
        window.write_event_value('-RECALL-OUT-', ("error", f"Recall error: {e}"))

# ---------------------
# Layout
# ---------------------
sg.theme('DarkTeal9')

# Recording Tab
record_layout = [
    [sg.Text("Duration (seconds):", size=(15,1)), sg.Slider(range=(1,60), orientation='h', key='-SECS-', default_value=10)],
    [sg.Button("📹 Start Recording", key='-REC-')],
    [sg.Text("", key='-REC-OUT-', size=(50,2))]
]

# Recall Tab
recall_layout = [
    [sg.Button("🗒️ Run Recall Assistant", key='-RECALL-')],
    [sg.Text("", key='-RECALL-OUT-', size=(50,2))],
    [sg.HorizontalSeparator()],
    [sg.Text("Recent Logs:", font=('Helvetica', 10, 'bold'))],
    [sg.Listbox(values=[], size=(40,6), key='-LOG-LIST-', enable_events=True)],
    [sg.Multiline("", size=(60,10), key='-LOG-VIEW-', disabled=True)]
]

# Settings Tab
settings_layout = [
    [sg.Text("Auto Loop Delay (s):"), sg.InputText(default_text="5", key='-LOOP-')],
    [sg.Text("Capture Mode:"), sg.Combo(['recording','screenshot'], default_value='recording', key='-MODE-')],
    [sg.Button("Save Settings", key='-SAVE-'), sg.Text("", key='-SAVE-OUT-')]
]

layout = [
    [sg.TabGroup([[ 
        sg.Tab('Record', record_layout), 
        sg.Tab('Recall', recall_layout), 
        sg.Tab('Settings', settings_layout) 
    ]], key='-TABS-', expand_x=True, expand_y=True)],
    [sg.Button("Exit")]
]

window = sg.Window("Observer Agent MVP", layout, resizable=True, finalize=True)

# Populate logs list on startup
def refresh_logs():
    logs = sorted(glob.glob(os.path.join('logs','*.json')), reverse=True)
    window['-LOG-LIST-'].update([os.path.basename(f) for f in logs])
refresh_logs()

# ---------------------
# Event Loop
# ---------------------
while True:
    event, values = window.read()
    if event in (sg.WINDOW_CLOSED, 'Exit'):
        break

    # Recording
    if event == '-REC-':
        secs = int(values['-SECS-'])
        threading.Thread(target=threaded_record, args=(window, secs), daemon=True).start()

    # Recall
    if event == '-RECALL-':
        threading.Thread(target=threaded_recall, args=(window,), daemon=True).start()

    # Display thread results
    if event == '-REC-OUT-':
        status, msg = values[event]
        color = {'info':'#00ffff','success':'#00ff00','error':'#ff4444'}[status]
        window['-REC-OUT-'].update(msg, text_color=color)
    if event == '-RECALL-OUT-':
        status, msg = values[event]
        color = {'info':'#00ffff','success':'#00ff00','error':'#ff4444'}[status]
        window['-RECALL-OUT-'].update(msg, text_color=color)
        refresh_logs()  # update log list after recall runs

    # Show selected log
    if event == '-LOG-LIST-':
        fname = values['-LOG-LIST-'][0]
        path = os.path.join('logs', fname)
        with open(path, 'r', encoding='utf-8') as f:
            window['-LOG-VIEW-'].update(f.read())

    # Settings
    if event == '-SAVE-':
        try:
            delay = float(values['-LOOP-'])
            mode  = values['-MODE-']
            # save to .env or config as needed
            with open('.env','w') as f:
                f.write(f"AUTO_LOOP_DELAY={delay}\nCAPTURE_MODE={mode}\n")
            window['-SAVE-OUT-'].update("Settings saved.", text_color='#00ff00')
        except Exception as e:
            window['-SAVE-OUT-'].update(f"Error: {e}", text_color='#ff4444')

window.close()
