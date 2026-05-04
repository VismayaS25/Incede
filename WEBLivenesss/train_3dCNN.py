import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader


class VideoDataset(Dataset):
    def __init__(self, X_path, y_path):
        self.X = np.load(X_path)
        self.y = np.load(y_path)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        video = self.X[idx]          # (T, H, W, C)
        label = self.y[idx]

        # Convert to PyTorch format
        video = torch.tensor(video, dtype=torch.float32)
        video = video.permute(3, 0, 1, 2)  # (T, H, W, C) to (C, T, H, W)

        label = torch.tensor(label, dtype=torch.long)
        return video, label


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

        # Input shape after convs:
        # (batch, 128, 4, 14, 14)
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




def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = VideoDataset(
        "OutputDatas/X.npy",
        "OutputDatas/y.npy"
    )

    loader = DataLoader(dataset, batch_size=4, shuffle=True)

    model = CNN3D().to(device)
    criterion = nn.CrossEntropyLoss()       #Traning
    optimizer = optim.Adam(model.parameters(), lr=1e-4)

    for epoch in range(10):
        model.train()
        total_loss = 0

        for videos, labels in loader:
            videos, labels = videos.to(device), labels.to(device)

            outputs = model(videos)
            loss = criterion(outputs, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(f"Epoch [{epoch+1}/10], Loss: {total_loss/len(loader):.4f}")

    # Model Saving
    torch.save(model.state_dict(), "antispoof_3dcnn.pth")
    print("Model saved as antispoof_3dcnn.pth")


if __name__ == "__main__":
    train()
