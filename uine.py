# ui.py
import os, glob, threading, json, webbrowser
import gradio as gr

from scripts.recording import start_screen_recording
from auto import run_workflow
from scripts.recall.__main__ import recall_query

LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

def record_and_summarize(duration_seconds):
    """
    1) Record for `duration_seconds`
    2) Run the full workflow (extract frames, summarize, insert to Snowflake, save JSON)
    3) Return the latest summary
    """
    # 1) Do the recording step
    start_screen_recording(duration_seconds=duration_seconds)

    # 2) Run the rest of the pipeline
    run_workflow()

    # 3) Pick up the latest JSON log and return it
    latest = sorted(glob.glob(os.path.join(LOGS_DIR, "*.json")), key=os.path.getctime)[-1]
    with open(latest, encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, indent=2)

def chat_with_ai(user_message):
    """
    Send `user_message` to recall_query, return its reply.
    """
    if not user_message.strip():
        return "(empty input)"
    return recall_query(user_message)

def list_logs():
    """
    Return a list of available JSON log filenames.
    """
    return sorted(os.listdir(LOGS_DIR), reverse=True)

def show_log_content(filename):
    """
    Load and return the contents of `logs/filename`.
    """
    path = os.path.join(LOGS_DIR, filename)
    if not os.path.exists(path):
        return f"File not found: {filename}"
    with open(path, encoding="utf-8") as f:
        return f.read()

with gr.Blocks(title="Observer Agent MVP") as demo:
    gr.Markdown("## Observer Agent MVP")

    with gr.Tabs():
        with gr.TabItem("📹 Record"):
            rec_slider = gr.Slider(1, 60, value=10, label="Duration (seconds)")
            rec_btn    = gr.Button("Start Recording & Summarize")
            rec_output = gr.Textbox(lines=10, label="Summary JSON")
            rec_btn.click(record_and_summarize, rec_slider, rec_output)

        with gr.TabItem("💬 Chat"):
            chat_in  = gr.Textbox(placeholder="Type your question here...", label="You")
            chat_btn = gr.Button("Send")
            chat_out = gr.Chatbot()
            def _chat_step(user, history=[]):
                history = history + [("You", user)]
                reply = chat_with_ai(user)
                history = history + [("AI", reply)]
                return history
            chat_btn.click(_chat_step, [chat_in, chat_out], chat_out)
            chat_in.submit(_chat_step, [chat_in, chat_out], chat_out)

        with gr.TabItem("📂 Logs"):
            log_dropdown = gr.Dropdown(choices=list_logs(), label="Select a log file")
            refresh_btn  = gr.Button("Refresh List")
            log_content  = gr.Code(label="Log Content (JSON)")
            refresh_btn.click(lambda: gr.update(choices=list_logs()), None, log_dropdown)
            log_dropdown.change(show_log_content, log_dropdown, log_content)

    # automatically open browser once the server is up
    def _open_browser():
        webbrowser.open_new_tab(demo.share_url or f"http://127.0.0.1:7860")
    threading.Timer(1.0, _open_browser).start()

if __name__ == "__main__":
    demo.launch(inbrowser=False, share=False)  # inbrowser=False because we open manually above
