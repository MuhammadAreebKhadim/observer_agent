"""
Extract image from video at a specific frame number.

Parameters:
- video_path: path to the video file
- output_path: path to the output image file
- frame_number: frame number to extract
- duration: duration of the video in seconds, e.g. 2-3 seconds
"""

import cv2
import os

def extract_frame(video_path, output_path, frame_number):
    """
    Extracts a specific frame from a video and saves it as an image.
    Args:
        video_path (str): Path to the video file.
        output_path (str): Path to save the extracted image.
        frame_number (int): Frame number to extract (0-based).
    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(video_path):
        print(f"[ERROR] Video file not found: {video_path}")
        return False
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video: {video_path}")
        return False
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_number < 0 or frame_number >= total_frames:
        print(f"[ERROR] Frame number {frame_number} is out of range (0-{total_frames-1})")
        cap.release()
        return False
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    if not ret:
        print(f"[ERROR] Could not read frame {frame_number}")
        cap.release()
        return False
    cv2.imwrite(output_path, frame)
    cap.release()
    print(f"[INFO] Frame {frame_number} saved to {output_path}")
    return True

def get_total_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return total_frames

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract a frame from a video file.")
    parser.add_argument("video_path", type=str, help="Path to the video file")
    parser.add_argument("output_path", type=str, help="Path to save the extracted image")
    parser.add_argument("frame_number", type=int, help="Frame number to extract (0-based)")
    args = parser.parse_args()
    extract_frame(args.video_path, args.output_path, args.frame_number)
