# ui.py
import os
import sys
import glob
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

from scripts.recording import start_screen_recording
from scripts.recall.__main__ import recall_query  # <- your new single‐query function

# ─── Custom Colors ────────────────────────────────────────────────────────────
BG       = "#2e2e2e"
FG       = "#f0f0f0"
ACCENT   = "#4e9a06"
ERROR    = "#cc0000"
SUCCESS  = "#00aa00"
INFO     = "#00aaff"

# ─── Main App ─────────────────────────────────────────────────────────────────
class ObserverAgentApp(ttk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        root.title("Observer Agent MVP")
        root.geometry("800x600")
        style = ttk.Style()
        style.theme_use('alt')
        style.configure('.', background=BG, foreground=FG, fieldbackground=BG)
        style.configure('TNotebook', background=BG)
        style.configure('TNotebook.Tab', background=BG, foreground=FG, padding=[12, 6])
        style.map('TNotebook.Tab',
                  background=[('selected', ACCENT)],
                  foreground=[('selected', BG)])
        style.configure('TSeparator', background=FG)
        self.create_widgets()
        self.pack(fill='both', expand=True)
        self.refresh_logs()

    def create_widgets(self):
        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=10, pady=10)

        # ── Tab 1: Record ────────────────────────────────────────────────────
        tab1 = ttk.Frame(nb)
        nb.add(tab1, text="📹 Record")

        ttk.Label(tab1, text="Duration (s):").grid(row=0, column=0, sticky='w', padx=10, pady=10)
        self.duration = tk.IntVar(value=10)
        ttk.Scale(tab1, from_=1, to=60, variable=self.duration, orient='horizontal')\
            .grid(row=0, column=1, sticky='ew', padx=10)
        tab1.columnconfigure(1, weight=1)

        self.rec_status = ttk.Label(tab1, text="", foreground=INFO)
        self.rec_status.grid(row=1, column=0, columnspan=2, sticky='w', padx=10)

        ttk.Button(tab1, text="Start Recording", command=self.on_record)\
            .grid(row=2, column=0, columnspan=2, pady=10)

        # ── Tab 2: Chat ──────────────────────────────────────────────────────
        tab2 = ttk.Frame(nb)
        nb.add(tab2, text="💬 Chat")

        self.chat_history = scrolledtext.ScrolledText(tab2, state='disabled', bg="#3b3b3b", fg=FG)
        self.chat_history.pack(fill='both', expand=True, padx=10, pady=(10,0))

        entry_frame = ttk.Frame(tab2)
        entry_frame.pack(fill='x', padx=10, pady=10)
        self.chat_entry = ttk.Entry(entry_frame)
        self.chat_entry.pack(side='left', fill='x', expand=True, padx=(0,10))
        self.chat_entry.bind('<Return>', lambda e: self.on_send())
        ttk.Button(entry_frame, text="Send", command=self.on_send).pack(side='right')

        # ── Tab 3: Logs ──────────────────────────────────────────────────────
        tab3 = ttk.Frame(nb)
        nb.add(tab3, text="📂 Logs")

        left = ttk.Frame(tab3)
        left.pack(side='left', fill='y', padx=(10,0), pady=10)
        self.log_list = tk.Listbox(left, bg="#3b3b3b", fg=FG, activestyle='none')
        self.log_list.pack(fill='y', expand=True)
        self.log_list.bind('<<ListboxSelect>>', self.on_select_log)

        right = ttk.Frame(tab3)
        right.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        self.log_view = scrolledtext.ScrolledText(right, state='disabled', bg="#3b3b3b", fg=FG)
        self.log_view.pack(fill='both', expand=True)

    # ─── Recording ──────────────────────────────────────────────────────────
    def on_record(self):
        secs = self.duration.get()
        threading.Thread(target=self._threaded_record, args=(secs,), daemon=True).start()

    def _threaded_record(self, secs):
        self.rec_status.config(text=f"Recording for {secs}s…", foreground=INFO)
        try:
            start_screen_recording(duration_seconds=secs)
            self.rec_status.config(text=f"✅ Saved recording ({secs}s)", foreground=SUCCESS)
        except Exception as e:
            self.rec_status.config(text=f"❌ Record error: {e}", foreground=ERROR)

    # ─── Chatbot ────────────────────────────────────────────────────────────
    def on_send(self):
        user_msg = self.chat_entry.get().strip()
        if not user_msg:
            return
        self._append_chat("You: " + user_msg + "\n", fg=FG)
        self.chat_entry.delete(0, 'end')
        threading.Thread(target=self._threaded_recall, args=(user_msg,), daemon=True).start()

    def _threaded_recall(self, user_msg):
        self._append_chat("AI: … thinking …\n", fg=INFO)
        try:
            answer = recall_query(user_msg)
            self._replace_last_ai(answer + "\n")
        except Exception as e:
            self._replace_last_ai(f"❌ Chat error: {e}\n", fg=ERROR)

    def _append_chat(self, text, fg=FG):
        self.chat_history.configure(state='normal')
        self.chat_history.insert('end', text)
        self.chat_history.tag_add(text, "end -1 lines", "end")
        self.chat_history.tag_config(text, foreground=fg)
        self.chat_history.configure(state='disabled')
        self.chat_history.see('end')

    def _replace_last_ai(self, text, fg=FG):
        self.chat_history.configure(state='normal')
        self.chat_history.delete("end -2 lines", "end -1 lines")
        self.chat_history.insert('end', "AI: " + text)
        self.chat_history.tag_add(text, "end -1 lines", "end")
        self.chat_history.tag_config(text, foreground=fg)
        self.chat_history.configure(state='disabled')
        self.chat_history.see('end')

    # ─── Logs ───────────────────────────────────────────────────────────────
    def refresh_logs(self):
        self.log_list.delete(0, 'end')
        for path in sorted(glob.glob(os.path.join("logs","*.json")), reverse=True):
            self.log_list.insert('end', os.path.basename(path))

    def on_select_log(self, _evt):
        sel = self.log_list.curselection()
        if not sel: return
        fname = self.log_list.get(sel[0])
        with open(os.path.join("logs", fname), encoding="utf-8") as f:
            data = f.read()
        self.log_view.configure(state='normal')
        self.log_view.delete("1.0", 'end')
        self.log_view.insert('end', data)
        self.log_view.configure(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app  = ObserverAgentApp(root)
    root.mainloop()
