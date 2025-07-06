# ui.py
import os
import sys
import glob
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from scripts.recording import start_screen_recording
from scripts.recall.__main__ import main as run_recall

class ObserverAgentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Observer Agent MVP")
        self.geometry("700x500")
        self.create_widgets()
        self.refresh_logs()

    def create_widgets(self):
        # ► Duration & Record
        frame1 = ttk.LabelFrame(self, text="Screen Recording")
        frame1.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame1, text="Duration (s):").pack(side="left", padx=(10,2))
        self.duration = tk.IntVar(value=10)
        ttk.Scale(frame1, from_=1, to=60, variable=self.duration, orient="horizontal").pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(frame1, text="📹 Record", command=self.on_record).pack(side="right", padx=10)
        
        # ► Recall Logs
        frame2 = ttk.LabelFrame(self, text="Recall Assistant")
        frame2.pack(fill="x", padx=10, pady=5)
        ttk.Button(frame2, text="🗒️ Run Recall", command=self.on_recall).pack(side="left", padx=10)
        
        # ► Log List + Viewer
        frame3 = ttk.LabelFrame(self, text="Logs Browser")
        frame3.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_list = tk.Listbox(frame3, height=6)
        self.log_list.pack(side="left", fill="y", padx=(10,0), pady=5)
        self.log_list.bind("<<ListboxSelect>>", self.on_select_log)

        self.log_view = scrolledtext.ScrolledText(frame3, state='disabled')
        self.log_view.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # ► Status bar
        self.status = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w")
        self.status_bar.pack(fill="x", side="bottom")

    def set_status(self, msg, kind="info"):
        colors = {"info":"black", "success":"green", "error":"red"}
        self.status_bar.configure(foreground=colors.get(kind, "black"))
        self.status.set(msg)

    def on_record(self):
        secs = self.duration.get()
        threading.Thread(target=self.threaded_record, args=(secs,), daemon=True).start()

    def threaded_record(self, secs):
        self.set_status(f"Recording for {secs}s…", "info")
        try:
            start_screen_recording(duration_seconds=secs)
            self.set_status(f"✅ Saved recording ({secs}s)", "success")
        except Exception as e:
            self.set_status(f"❌ Record error: {e}", "error")

    def on_recall(self):
        threading.Thread(target=self.threaded_recall, daemon=True).start()

    def threaded_recall(self):
        self.set_status("Running recall…", "info")
        try:
            run_recall()
            self.set_status("✅ Recall complete", "success")
            self.refresh_logs()
        except Exception as e:
            self.set_status(f"❌ Recall error: {e}", "error")

    def refresh_logs(self):
        self.log_list.delete(0, tk.END)
        paths = sorted(glob.glob(os.path.join("logs","*.json")), reverse=True)
        for p in paths:
            self.log_list.insert(tk.END, os.path.basename(p))

    def on_select_log(self, _evt):
        sel = self.log_list.curselection()
        if not sel: return
        fname = self.log_list.get(sel[0])
        with open(os.path.join("logs", fname), encoding="utf-8") as f:
            text = f.read()
        self.log_view.configure(state='normal')
        self.log_view.delete("1.0", tk.END)
        self.log_view.insert(tk.END, text)
        self.log_view.configure(state='disabled')

if __name__ == "__main__":
    app = ObserverAgentApp()
    app.mainloop()
