import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class CNNModel(nn.Module):
    def __init__(self, input_height, input_width, num_classes):
        super(CNNModel, self).__init__()

        self.conv1 = nn.Conv2d(in_channels=1, out_channels=8, kernel_size=(3, 3))
        self.pool1 = nn.MaxPool2d(kernel_size=(3, 3))

        self.conv2 = nn.Conv2d(in_channels=8, out_channels=16, kernel_size=(3, 3))
        self.pool2 = nn.MaxPool2d(kernel_size=(3, 3))

        with torch.no_grad():
            dummy = torch.zeros(1, 1, input_height, input_width)
            dummy = self.pool1(F.relu(self.conv1(dummy)))
            dummy = self.pool2(F.relu(self.conv2(dummy)))
            self.flatten_dim = dummy.view(1, -1).shape[1]

        self.fc1 = nn.Linear(self.flatten_dim, 64)
        self.fc2 = nn.Linear(64, 128)
        self.fc3 = nn.Linear(128, num_classes)

    def forward(self, x):
        # x shape: (batch, height, width)
        x = x.unsqueeze(1)  # reshape to (batch, 1, height, width)
        x = F.relu(self.conv1(x))
        x = self.pool1(x)
        x = F.relu(self.conv2(x))
        x = self.pool2(x)
        x = torch.flatten(x, start_dim=1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)  # raw logits, no softmax here
        return x


def load_model(checkpoint_path, device):
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)

    model = CNNModel(
        input_height=checkpoint["input_height"],
        input_width=checkpoint["input_width"],
        num_classes=checkpoint["num_classes"]
    ).to(device)

    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    classes = checkpoint["classes"]
    return model, classes, checkpoint

if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    working_dir = "/home/pi/prelab10"
    model_filename = "20230306_043352_Prelab10_CNN_model1.pth"
    model_path = os.path.join(working_dir, model_filename)

    model, classes, checkpoint = load_model(model_path, device)

    print("Model loaded successfully.")
    print("Model path:", model_path)
    print("Input height:", checkpoint["input_height"])
    print("Input width:", checkpoint["input_width"])
    print("Number of classes:", checkpoint["num_classes"])
    print("Classes:", classes)
    print(model)