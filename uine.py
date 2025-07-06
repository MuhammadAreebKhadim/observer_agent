# ui.py
import os
import sys
import glob
import threading
import json                                # ← ADD: for parsing the JSON log
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText


from scripts.recording import start_screen_recording
from auto import run_workflow              # ← ADD: full end-to-end pipeline
from scripts.recall.__main__ import recall_query

# ─── Theming ───────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FG = "#f0f0f0"
BG = "#2e2e2e"
ACCENT = "#4e9a06"
SUCCESS = "#00aa00"
ERROR   = "#ff4444"
INFO    = "#00aaff"

class ObserverAgentApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Observer Agent MVP")
        self.geometry("900x650")
        self._build_ui()
        self._refresh_logs()

    def _build_ui(self):
        self.tabs = ctk.CTkTabview(self, width=800)
        self.tabs.pack(padx=20, pady=20, fill="both", expand=True)
        self.tabs.add("Record"); self.tabs.add("Chat"); self.tabs.add("Logs")

        # ─── Record Tab ───────────────────────────────────────
        rec_tab = self.tabs.tab("Record")
        rec_tab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(rec_tab, text="Duration (s):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.duration = ctk.CTkSlider(rec_tab, from_=1, to=60, number_of_steps=59)
        self.duration.set(10)
        self.duration.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.rec_btn = ctk.CTkButton(rec_tab, text="📹 Start Recording", corner_radius=12,
                                     command=self._on_record)   # ← MODIFIED
        self.rec_btn.grid(row=1, column=0, columnspan=2, pady=(0,10))

        self.rec_status = ctk.CTkLabel(rec_tab, text="", text_color=INFO)
        self.rec_status.grid(row=2, column=0, columnspan=2, padx=10, sticky="w")

        # ─── Chat Tab ─────────────────────────────────────────
        chat_tab = self.tabs.tab("Chat")
        self.chat_history = ctk.CTkTextbox(chat_tab, wrap="word", state="disabled", corner_radius=12)
        self.chat_history.pack(padx=20, pady=(20,10), fill="both", expand=True)

        entry_frame = ctk.CTkFrame(chat_tab, corner_radius=12)
        entry_frame.pack(padx=20, pady=(0,20), fill="x")
        self.chat_entry = ctk.CTkEntry(entry_frame, placeholder_text="Type your question here...")
        self.chat_entry.pack(side="left", padx=(10,5), fill="x", expand=True)
        self.chat_entry.bind("<Return>", lambda e: self._on_send())
        ctk.CTkButton(entry_frame, text="Send", corner_radius=12, command=self._on_send).pack(side="right", padx=(5,10))

        # ─── Logs Tab ─────────────────────────────────────────
        logs_tab = self.tabs.tab("Logs")
        logs_tab.grid_columnconfigure(1, weight=1)

        list_frame = ctk.CTkFrame(logs_tab, corner_radius=12, fg_color="#3a3a3a")
        list_frame.grid(row=0, column=0, padx=(20,5), pady=20, sticky="ns")

        self.log_list = tk.Listbox(
            list_frame,
            bg="#3a3a3a",
            fg=FG,
            highlightthickness=0,
            bd=0,
            selectbackground=ACCENT,
            selectforeground=BG
        )
        self.log_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_list.bind("<<ListboxSelect>>", lambda e: self._on_select_log())

        self.log_view = ctk.CTkTextbox(
            logs_tab,
            wrap="none",
            state="disabled",
            corner_radius=12,
            fg_color="#3a3a3a",
            text_color=FG
        )
        self.log_view.grid(row=0, column=1, padx=(5,20), pady=20, sticky="nsew")

    # ─── Record Handler ────────────────────────────────────
    def _on_record(self):
        secs = int(self.duration.get())
        self.rec_status.configure(text=f"Running workflow for {secs}s…", text_color=INFO)
        threading.Thread(target=self._threaded_full_workflow, args=(secs,), daemon=True).start()

    def _threaded_full_workflow(self, secs):
        try:
            run_workflow()
            latest = sorted(glob.glob(os.path.join("logs","*.json")), key=os.path.getctime)[-1]
            with open(latest, encoding="utf-8") as f:
                data = json.load(f)
            summary = json.dumps(data, indent=2)

            # pop up a Tk window with scrollable JSON
            self.after(0, lambda: self._show_summary(summary))

            self.rec_status.configure(text="✅ Workflow complete", text_color=SUCCESS)
            self._refresh_logs()
        except Exception as e:
            self.rec_status.configure(text=f"❌ Workflow error: {e}", text_color=ERROR)


    # ─── Chat Handlers ────────────────────────────────────
    def _on_send(self):
        user_msg = self.chat_entry.get().strip()
        if not user_msg:
            return
        self._append_chat("You: " + user_msg + "\n", FG)
        self.chat_entry.delete(0, "end")
        threading.Thread(target=self._threaded_chat, args=(user_msg,), daemon=True).start()

    def _threaded_chat(self, msg):
        self._append_chat("AI: thinking...\n", INFO)
        try:
            reply = recall_query(msg)
            if not reply.strip():
                reply = "(no response)"
            self._replace_last_ai("AI: " + reply + "\n", SUCCESS)
        except Exception as e:
            self._replace_last_ai(f"AI: Error: {e}\n", ERROR)


    def _append_chat(self, text, color):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", text)
        self.chat_history.tag_add(text, "end-1c linestart", "end-1c lineend")
        self.chat_history.tag_config(text, foreground=color)
        self.chat_history.configure(state="disabled")
        self.chat_history.yview("end")

    def _replace_last_ai(self, text, color):
        self.chat_history.configure(state="normal")
        self.chat_history.delete("end-2l", "end-1l")
        self.chat_history.insert("end", text)
        self.chat_history.tag_add(text, "end-1c linestart", "end-1c lineend")
        self.chat_history.tag_config(text, foreground=color)
        self.chat_history.configure(state="disabled")
        self.chat_history.yview("end")

    # ─── Logs Handlers ────────────────────────────────────
    def _refresh_logs(self):
        self.log_list.delete(0, "end")
        for path in sorted(glob.glob("logs/*.json"), reverse=True):
            self.log_list.insert("end", os.path.basename(path))

    def _on_select_log(self):
        sel = self.log_list.curselection()
        if not sel: return
        fname = self.log_list.get(sel[0])
        with open(os.path.join("logs", fname), encoding="utf-8") as f:
            content = f.read()
        self.log_view.configure(state="normal")
        self.log_view.delete("0.0", "end")
        self.log_view.insert("0.0", content)
        self.log_view.configure(state="disabled")
        
    def _show_summary(self, summary_text):
        win = tk.Toplevel(self)
        win.title("Summary")
        win.geometry("600x400")
        txt = ScrolledText(win, wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", summary_text)
        txt.configure(state="disabled")
        tk.Button(win, text="Close", command=win.destroy).pack(pady=(0,10))


if __name__ == "__main__":
    app = ObserverAgentApp()
    app.mainloop()
