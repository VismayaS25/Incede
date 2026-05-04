import torch
import torch.nn as nn
import numpy as np
import cv2
from fastapi import FastAPI, UploadFile, File         #Backend framework
from typing import List
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware        #CORS : allows browser frontend to call backend

#CONFIG
# MODEL_PATH = "E:\\INCEDE\\WEBLivenesss\\antispoof_3dcnn.pth"
MODEL_PATH = "antispoof_3dcnn.pth"

IMG_SIZE = 112
NUM_FRAMES = 16
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")   #to use GPU if needed

# OCCLUSION MODEL CONFIG
# OCC_MODEL_PATH = "E:\\INCEDE\\WEBLivenesss\\occlusion_model.pth"
OCC_MODEL_PATH = "occlusion_model.pth"

OCC_IMG_SIZE = 96

occ_classes = ["normal", "mask", "hand", "sunglasses", "glasses", "other"]

app = FastAPI(title="Face Liveness Anti-Spoofing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#MODEL
class CNN3D(nn.Module):
    def __init__(self):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv3d(3, 32, kernel_size=3, padding=1),   #RGB
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
        x = x.view(x.size(0), -1)
        return self.classifier(x)

#LOAD MODEL 
# model = CNN3D().to(DEVICE)
# # state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
# model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
# model.eval()

model = CNN3D().to(DEVICE)
state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
model.load_state_dict(state_dict, strict=False)
model.eval()

# OCCLUSION MODEL
class OcclusionCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3,32,3,1,1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32,64,3,1,1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64,128,3,1,1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Flatten(),
            nn.Linear(128*12*12,256),
            nn.ReLU(),
            nn.Linear(256,6)
        )

    def forward(self,x):
        return self.net(x)

occ_model = OcclusionCNN().to(DEVICE)
# checkpoint = torch.load(OCC_MODEL_PATH, map_location=DEVICE)
# occ_model.load_state_dict(checkpoint["model"])
# occ_model.eval()
checkpoint = torch.load(OCC_MODEL_PATH, map_location=DEVICE)

if isinstance(checkpoint, dict) and "model" in checkpoint:
    occ_model.load_state_dict(checkpoint["model"], strict=False)
else:
    occ_model.load_state_dict(checkpoint, strict=False)

occ_model.eval()

#Preprocessing
def preprocess_frames(frames: List[np.ndarray]):
    processed = []

    for frame in frames:
        frame = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = frame / 255.0
        processed.append(frame)

    while len(processed) < NUM_FRAMES:
        processed.append(processed[-1])

    processed = np.array(processed[:NUM_FRAMES])
    tensor = torch.tensor(processed, dtype=torch.float32)
    tensor = tensor.permute(3, 0, 1, 2).unsqueeze(0)          #(1,3,16,112,112)
    return tensor.to(DEVICE)

# Checking Occlusion
def check_occlusion(frame):
    img = cv2.resize(frame, (OCC_IMG_SIZE, OCC_IMG_SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img / 255.0

    # NORMALIZATION 
    img = (img - 0.5) / 0.5
    tensor = torch.tensor(img, dtype=torch.float32)
    tensor = tensor.permute(2,0,1).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        out = occ_model(tensor)
        probs = torch.softmax(out, dim=1)
        conf, pred = torch.max(probs, 1)
    label = occ_classes[pred.item()]
    confidence = conf.item()

    print("OCC:", label, confidence)

     #  Reject only if strong occlusion detected
    if label in ["mask", "hand", "other"] and confidence > 0.60:
        return label

    if label in ["sunglasses", "glasses"] and confidence > 0.75:
        return label

    # Otherwise allow
    return "normal"

# Occlusion 
@app.post("/check_occlusion")
async def check_occlusion_api(file: UploadFile = File(...)):
    try:
        content = await file.read()
        np_arr = np.frombuffer(content, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"status":"error"}

        label = check_occlusion(frame)

        if label == "normal":
            return {"status":"ok"}
        else:
            return {
                "status":"covered",
                "reason": " face not clear "
            }

    except Exception as e:
        return {"status":"error", "msg": str(e)}

# API
@app.post("/verify")
async def verify(files: List[UploadFile] = File(...)):        #Receives multiple images
    try:
        print(" Files received:", len(files))
        frames = []

        for i, file in enumerate(files):
            content = await file.read()

            if len(content) < 1000:
                print(f"Frame {i} too small, skipped")
                continue
            np_arr = np.frombuffer(content, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                print(f"Frame {i} decode failed")     #Skips corrupted frames
                continue
            frames.append(frame)
        
        print("Valid frames:", len(frames))
        
        if len(frames) == 0:
            return JSONResponse(
                status_code=400,
                content={"error": "No valid frames received"}
            )
       
        while len(frames) < NUM_FRAMES:
            frames.append(frames[-1])
        frames = frames[:NUM_FRAMES]
        input_tensor = preprocess_frames(frames)

        print("Input tensor shape:", input_tensor.shape)

        with torch.no_grad():
            output = model(input_tensor)
            probs = torch.softmax(output, dim=1)
            live_score = probs[0, 1].item()

        print("Live score:", live_score)

        return {
            "prediction": "LIVE" if live_score > 0.65 else "SPOOF",
            "live_score": round(live_score, 3)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )



