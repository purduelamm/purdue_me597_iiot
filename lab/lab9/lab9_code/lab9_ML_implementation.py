import time
import board
import busio
import adafruit_adxl34x
from micropython import const
import datetime
import numpy as np
from scipy import stats
import torch
import torch.nn as nn

# =========================
# Device
# =========================
device = torch.device("cpu")

# =========================
# Sensor setup
# =========================
i2c = busio.I2C(board.SCL, board.SDA)
acc = adafruit_adxl34x.ADXL345(i2c)
acc.data_rate = const(0b1111)

ratedict = {
    15: 3200, 14: 1600, 13: 800, 12: 400,
    11: 200, 10: 100, 9: 50, 8: 25,
    7: 12.5, 6: 6.25, 5: 3.13, 4: 1.56,
    3: 0.78, 2: 0.39, 1: 0.2, 0: 0.1
}

print("Output data rate is {} Hz".format(ratedict[acc.data_rate]))

# =========================
# Model definition
# Must match the saved model exactly
# =========================
EMBEDDING_SIZE = 64
N_feature = 500   # freqFeatures(x) with N=1000 -> N//2 = 500

class AnomalyDetector(nn.Module):
    def __init__(self, n_feature):
        super(AnomalyDetector, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(n_feature, 256),
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
            nn.Linear(256, n_feature),
            nn.Sigmoid()
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

# =========================
# Utility functions
# =========================
def measureData(sensor: object, N: int):
    data_x, data_y, data_z = [], [], []
    for _ in range(N):
        x_acc, y_acc, z_acc = sensor.acceleration
        data_x.append(x_acc)
        data_y.append(y_acc)
        data_z.append(z_acc)

    x_data = np.array(data_x, dtype=np.float32)
    y_data = np.array(data_y, dtype=np.float32)
    z_data = np.array(data_z, dtype=np.float32)
    return x_data, y_data, z_data

def timeFeatures(data):
    mean = np.mean(data)
    std = np.std(data)
    rms = np.sqrt(np.mean(data ** 2))
    peak = np.max(np.abs(data))
    skew = stats.skew(data)
    kurt = stats.kurtosis(data)
    cf = peak / rms if rms != 0 else 0.0
    feature = np.array([mean, std, rms, peak, skew, kurt, cf], dtype=np.float32)
    return feature

def freqFeatures(data):
    N = len(data)
    yf = 2.0 / N * np.abs(np.fft.fft(data)[:N // 2])
    yf[0] = 0
    feature = np.array(yf, dtype=np.float32)
    return feature

def tensorNormalization(data, min_val, max_val):
    data_normal = (data - min_val) / (max_val - min_val + 1e-8)
    tensor = torch.tensor(data_normal, dtype=torch.float32).view(1, -1)
    return tensor

def predict(model, data, threshold):
    model.eval()
    with torch.no_grad():
        data = data.to(device)
        reconstruction = model(data)
        loss = torch.mean(torch.abs(reconstruction - data), dim=1)
        result = torch.lt(loss, threshold)
    return bool(result.item()), float(loss.item())

# =========================
# Main
# =========================
if __name__ == "__main__":
    model_path = "/home/pi/lab9/models/20260414_220026_lab8_anomaly_x-axis_raw.pth"

    loaded_model = AnomalyDetector(N_feature)
    loaded_model.load_state_dict(torch.load(model_path, map_location=device))
    loaded_model.to(device)
    loaded_model.eval()

    print("Model reload success.")

    # Use the values you already computed
    min_val = -20.08401870727539
    max_val = 17.25970458984375

    # Replace this with your actual threshold
    threshold = 0.12

    while True:
        try:
            x, y, z = measureData(acc, 1000)

            # Current pipeline uses X-axis frequency feature
            input_feature = freqFeatures(x)

            input_feature_normalized = tensorNormalization(input_feature, min_val, max_val)
            result, loss = predict(loaded_model, input_feature_normalized, threshold)

            now = datetime.datetime.now()
            print("{0}: Model result={1}, MAE loss={2:.4f}".format(now, result, loss))

            time.sleep(1)

        except KeyboardInterrupt:
            raise