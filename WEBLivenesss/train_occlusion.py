import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms
from torch.utils.data import Dataset, DataLoader

DATASET_PATH = "E:\INCEDE\WEBLivenesss\occlusion_dataset"
IMG_SIZE = 96
BATCH_SIZE = 8
EPOCHS = 4
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

classes = ["normal", "mask", "hand", "sunglasses", "glasses", "other"]
class_to_idx = {c:i for i,c in enumerate(classes)}

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize([0.5,0.5,0.5],[0.5,0.5,0.5])
])

class OccDataset(Dataset):
    def __init__(self):
        self.images=[]
        self.labels=[]
        for cls in classes:
            folder=os.path.join(DATASET_PATH,cls)
            for img in os.listdir(folder):
                self.images.append(os.path.join(folder,img))
                self.labels.append(class_to_idx[cls])

    def __len__(self):
        return len(self.images)

    def __getitem__(self,idx):
        img=cv2.imread(self.images[idx])
        img=cv2.resize(img,(IMG_SIZE,IMG_SIZE))
        img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        img=transform(img)
        label=torch.tensor(self.labels[idx])
        return img,label


dataset = OccDataset()

print("Total images:", len(dataset)) 

loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

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
        nn.Linear(128*12*12,256),   # ← FIXED
        nn.ReLU(),
        nn.Linear(256,len(classes))
    )


    def forward(self,x):
        return self.net(x)

model = OcclusionCNN().to(DEVICE)
opt = torch.optim.Adam(model.parameters(), lr=0.001)
loss_fn = nn.CrossEntropyLoss()

for epoch in range(EPOCHS):
    total=0
    correct=0
    model.train()

    for imgs, labels in loader:
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)

        preds = model(imgs)
        loss = loss_fn(preds, labels)

        opt.zero_grad()
        loss.backward()
        opt.step()

        _,p = preds.max(1)
        correct += (p==labels).sum().item()
        total += labels.size(0)

    print(f"Epoch {epoch+1} acc:", correct/total)

torch.save({ "model": model.state_dict(), "classes": classes}, "occlusion_model.pth")

print("occlusion_model.pth saved")
