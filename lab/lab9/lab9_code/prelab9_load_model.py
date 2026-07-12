import torch
import torch.nn as nn

EMBEDDING_SIZE = 64
N_feature = 1000

class AnomalyDetector(nn.Module):
    def __init__(self, N_feature):
        super(AnomalyDetector, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(N_feature, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, EMBEDDING_SIZE),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(EMBEDDING_SIZE, 128),
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, N_feature),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))
        
# device setting
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# model path
model_path = r"20260414_220026_lab8_anomaly_x-axis_raw.pth"

# load model
loaded_model = AnomalyDetector(N_feature)
loaded_model.load_state_dict(torch.load(model_path, map_location=device))
loaded_model.to(device)
loaded_model.eval()

print("Model reload success.")
