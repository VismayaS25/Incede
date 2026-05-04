# Load Dataset
import numpy as np

X = np.load(r"E:\INCEDE\WEBLivenesss\OutputDatas\X.npy")
y = np.load(r"E:\INCEDE\WEBLivenesss\OutputDatas\y.npy")

print("Dataset shape:", X.shape)
print("Labels shape:", y.shape)


# Split dataset for evaluation
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Test samples:", len(X_test))


# Load trained model
import torch
from inference_3dCNN import CNN3D

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = CNN3D().to(device)

model.load_state_dict(
    torch.load("antispoof_3dcnn.pth", map_location=device)
)

model.eval()


# Run inference on test data
y_pred = []
live_scores = []

for i in range(len(X_test)):

    # Convert numpy → tensor
    input_tensor = torch.tensor(X_test[i])

    # IMPORTANT: reorder dimensions
    input_tensor = input_tensor.permute(3,0,1,2)

    # Add batch dimension
    input_tensor = input_tensor.unsqueeze(0).float().to(device)

    with torch.no_grad():

        output = model(input_tensor)

        probs = torch.softmax(output, dim=1)

        live_score = probs[0,1].item()

    prediction = 1 if live_score > 0.65 else 0

    y_pred.append(prediction)
    live_scores.append(live_score)


# Compute performance metrics
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score

print("\nPerformance Metrics")
print("-------------------")

print("Accuracy :", accuracy_score(y_test, y_pred))
print("Precision:", precision_score(y_test, y_pred))
print("Recall   :", recall_score(y_test, y_pred))
print("F1 Score :", f1_score(y_test, y_pred))


# Generate confusion matrix
from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

cm = confusion_matrix(y_test, y_pred)

plt.figure(figsize=(5,4))

sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=["Spoof","Live"],
    yticklabels=["Spoof","Live"]
)

plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")

plt.savefig("confusion_matrix.png")

plt.show()


# ROC Curve
from sklearn.metrics import roc_curve, auc

fpr, tpr, _ = roc_curve(y_test, live_scores)

roc_auc = auc(fpr, tpr)

plt.figure()

plt.plot(fpr, tpr, label=f"ROC Curve (AUC = {roc_auc:.2f})")
plt.plot([0,1],[0,1],'--')

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve")

plt.legend()

plt.savefig("roc_curve.png")

plt.show()