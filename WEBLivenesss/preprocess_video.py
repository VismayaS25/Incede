import cv2
import os
import numpy as np
from tqdm import tqdm

# CONFIG
DATASET_DIR = "E:\INCEDE\WEBLivenesss\Dataset"
OUTPUT_DIR = "E:\INCEDE\WEBLivenesss\OutputDatas"
IMG_SIZE = 112
NUM_FRAMES = 16

os.makedirs(OUTPUT_DIR, exist_ok=True)

X = []
y = []

def extract_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames < NUM_FRAMES:
        cap.release()
        return None

    frame_idxs = np.linspace(0, total_frames - 1, NUM_FRAMES).astype(int)      #Frame extraction

    idx = 0
    grabbed = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        #Frame preprocessing
        if idx in frame_idxs:
            frame = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = frame / 255.0
            frames.append(frame)
            grabbed += 1

        idx += 1
        if grabbed == NUM_FRAMES:
            break

    cap.release()

    if len(frames) == NUM_FRAMES:
        return np.array(frames)
    return None


for label_name, label in [("live", 1), ("spoof", 0)]:
    folder = os.path.join(DATASET_DIR, label_name)

    for video in tqdm(os.listdir(folder), desc=f"Processing {label_name}"):
        video_path = os.path.join(folder, video)
        frames = extract_frames(video_path)

        if frames is not None:
            X.append(frames)
            y.append(label)

X = np.array(X)             #(N,16,112,112,3)
y = np.array(y)             #(N,)

np.save(os.path.join(OUTPUT_DIR, "X.npy"), X)
np.save(os.path.join(OUTPUT_DIR, "y.npy"), y)

print("Preprocessing complete")
print("X shape:", X.shape)
print("y shape:", y.shape)
