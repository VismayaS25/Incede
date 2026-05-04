import cv2
import numpy as np
import torch
import torch.nn as nn

#CONFIG
MODEL_PATH = "antispoof_3dcnn.pth"
IMG_SIZE = 112
NUM_FRAMES = 16
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


#MODEL
class CNN3D(nn.Module):
    def __init__(self):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv3d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm3d(32),
            nn.ReLU(),
            nn.MaxPool3d((1, 2, 2)),

            nn.Conv3d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm3d(64),
            nn.ReLU(),
            nn.MaxPool3d((2, 2, 2)),

            nn.Conv3d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm3d(128),
            nn.ReLU(),
            nn.MaxPool3d((2, 2, 2)),
        )

        self.classifier = nn.Sequential(
            nn.Linear(128 * 4 * 14 * 14, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 2)
        )

    def forward(self, x):
        x = self.features(x)
        x = torch.flatten(x, 1)
        return self.classifier(x)


#FRAME EXTRACTION
def extract_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        cap.release()
        raise ValueError("Empty Video")

    frame_idxs = np.linspace(0, max(total_frames - 1, 0), NUM_FRAMES).astype(int)
    idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if idx in frame_idxs:
            frame = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = frame / 255.0
            frames.append(frame)

        idx += 1
        if len(frames) == NUM_FRAMES:
            break

    cap.release()

    # Repeat last frame if still video frame short
    while len(frames) < NUM_FRAMES:
        frames.append(frames[-1])
    return np.array(frames)


    

#INFERENCE
def predict(video_path):
    frames = extract_frames(video_path)

    frames = torch.tensor(frames, dtype=torch.float32)
    frames = frames.permute(3, 0, 1, 2).unsqueeze(0)  # (1, C, T, H, W)
    frames = frames.to(DEVICE)

    model = CNN3D().to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    with torch.no_grad():
        outputs = model(frames)
        probs = torch.softmax(outputs, dim=1)
        live_score = probs[0][1].item()           #Probability of LIVE class

    prediction = "LIVE" if live_score > 0.5 else "SPOOF"
    return prediction, live_score


#MAIN
if __name__ == "__main__":
    live_pred, live_score = predict("E:\INCEDE\WEBLivenesss\Dataset\Live\live_video1.mp4")
    replay_pred, replay_score = predict("E:\INCEDE\WEBLivenesss\Dataset\Spoof\spoof_video5.mp4")

    print(f"LIVE video → Prediction: {live_pred}, Score: {live_score:.3f}")
    print(f"REPLAY video → Prediction: {replay_pred}, Score: {replay_score:.3f}")
