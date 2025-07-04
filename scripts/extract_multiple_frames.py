import os
import sys

# Determine project root (one level up from this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

sys.path.append(SCRIPT_DIR)
from extract_image_from_video import extract_frame, get_total_frames

RECORDINGS_DIR = os.path.join(PROJECT_ROOT, 'recordings')
SCREENSHOTS_DIR = os.path.join(RECORDINGS_DIR, 'screenshots')
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Number of screenshots to extract per video
NUM_FRAMES = 5

def extract_frames_from_video(video_path, out_dir, num_frames=5):
    total_frames = get_total_frames(video_path)
    if total_frames == 0:
        print(f"[ERROR] Could not open video: {video_path}")
        return
    if total_frames < num_frames:
        frame_indices = list(range(total_frames))
    else:
        frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]
    base = os.path.splitext(os.path.basename(video_path))[0]
    for idx, frame_num in enumerate(frame_indices):
        out_path = os.path.join(out_dir, f"{base}_frame_{frame_num}.jpg")
        extract_frame(video_path, out_path, frame_num)

def main():
    for fname in os.listdir(RECORDINGS_DIR):
        if fname.lower().endswith('.mp4'):
            video_path = os.path.join(RECORDINGS_DIR, fname)
            extract_frames_from_video(video_path, SCREENSHOTS_DIR, NUM_FRAMES)

if __name__ == "__main__":
    main() 