# ui.py
import gradio as gr
from scripts.recording import start_screen_recording
from scripts.recall.__main__ import main as run_recall

def record(seconds: int = 10):
    start_screen_recording(duration_seconds=seconds)
    return f"Recorded for {seconds}s → check recordings/"

def recall_logs():
    run_recall()
    return "Recall complete! See logs/"

with gr.Blocks(title="Observer Agent MVP") as app:
    gr.Markdown("# Observer Agent MVP Dashboard")
    with gr.Row():
        seconds = gr.Slider(1, 60, value=10, label="Record Duration (s)")
        rec_btn = gr.Button("📹 Record")
    rec_out = gr.Textbox(label="Recorder Output")

    with gr.Row():
        recall_btn = gr.Button("🗒️ Run Recall")
    recall_out = gr.Textbox(label="Recall Output")

    rec_btn.click(record, inputs=seconds, outputs=rec_out)
    recall_btn.click(recall_logs, outputs=recall_out)

if __name__ == "__main__":
    app.launch()
