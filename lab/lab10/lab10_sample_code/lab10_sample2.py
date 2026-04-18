from xml.etree import ElementTree as ET
import requests
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import math
import time
import torch
import torch.nn as nn
import torch.nn.functional as F


## == GLOBAL CONSTANT ==
SAMPLE = "sample" # sample string for MTConnect HTML sample method
CURRENT = "current" # current string for MTConnect HTML current method
SAMP_RATE = int(48000) # sampling rate
CHUNK = int(2 ** 11) # chunk size
AGENT = "http://10.165.67.146:5001/" # MTConnect agent ip:port

N = 23 # number of sequence to take sound
N_FFT = 2048 # number of FFT
N_MELS = 128 # number of Mel filter bank


class CNNModel(nn.Module):
    def __init__(self, input_height, input_width, num_classes):
        super(CNNModel, self).__init__()

        self.conv1 = nn.Conv2d(in_channels=1, out_channels=8, kernel_size=(3, 3))   # first 2D CNN layer
        self.pool1 = nn.MaxPool2d(kernel_size=(3, 3))                                # max pooling layer

        self.conv2 = nn.Conv2d(in_channels=8, out_channels=16, kernel_size=(3, 3))   # second 2D CNN layer
        self.pool2 = nn.MaxPool2d(kernel_size=(3, 3))                                 # max pooling layer

        with torch.no_grad():
            dummy = torch.zeros(1, 1, input_height, input_width)
            dummy = self.pool1(F.relu(self.conv1(dummy)))
            dummy = self.pool2(F.relu(self.conv2(dummy)))
            self.flatten_dim = dummy.view(1, -1).shape[1]

        self.fc1 = nn.Linear(self.flatten_dim, 64)                                    # first hidden layer
        self.fc2 = nn.Linear(64, 128)                                                 # second hidden layer
        self.fc3 = nn.Linear(128, num_classes)                                        # output layer

    def forward(self, x):
        # x shape: (batch, height, width)
        x = x.unsqueeze(1)                        # reshape to (batch, 1, height, width)
        x = F.relu(self.conv1(x))
        x = self.pool1(x)
        x = F.relu(self.conv2(x))
        x = self.pool2(x)
        x = torch.flatten(x, start_dim=1)        # flatten layer
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)                          # raw logits, no softmax here
        return x


# custom function and class to make the code concise

def get_sound_signal(response): # taking sound signal of a series of the MTConnect sequences
    root = ET.fromstring(response.content)
    MTCONNECT_STR = root.tag.split("}")[0] + "}"
    array = []
    for sample in root.iter(MTCONNECT_STR + "DisplacementTimeSeries"):
        chunk = np.fromstring(sample.text, dtype=np.int16, sep=' ') / (2 ** 15)
        array = np.append(array, chunk)
    array = np.array(array, dtype=np.float32)
    return array # sound signal as float array


def get_sound_level(signal):
    signal_rms = np.sqrt(np.mean(signal ** 2))
    sound_level = 20 * math.log10(signal_rms / 9.9963e-7) - 28.87
    return sound_level


def feature_extraction(x): # feature extraction for CNN model. This must be the same as you trained the model
    M = librosa.feature.melspectrogram(
        y=x,
        sr=SAMP_RATE,
        n_fft=N_FFT,
        hop_length=int(N_FFT / 4),
        win_length=N_FFT,
        window='hann',
        n_mels=N_MELS
    ) # Mel-spectrogram

    X = 2 * abs(M) / N_FFT # Taking magnitude for the input feature of the CNN model
    X = np.array(X, dtype=np.float32)
    S = np.reshape(X, (1, X.shape[0], X.shape[1])) # reshaping (1, n, m) : The first dimension is batch size
    return S # input feature of the CNN model as 3D tensor


class CurrentParsing(object): # MTConnect current Object to get last sequence and timestamp
    def __init__(self, response):
        root = ET.fromstring(response.content)
        MTCONNECT_STR = root.tag.split("}")[0] + "}"
        header = root.find("./" + MTCONNECT_STR + "Header")
        header_attribs = header.attrib
        self.nextSeq = int(header_attribs["nextSequence"])
        self.firstSeq = int(header_attribs["firstSequence"])
        self.lastSeq = int(header_attribs["lastSequence"])
        for sample in root.iter(MTCONNECT_STR + "DisplacementTimeSeries"):
            self.timestamp = sample.get('timestamp')


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
    model_file = '20230309_212154_Prelab10_CNN_model1.pth' # PyTorch checkpoint file name. Note that this file must be in the same directory

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, classes, checkpoint = load_model(model_file, device)

    print("Model loaded successfully.")
    print("Classes:", classes)

    while True:
        Current = CurrentParsing(
            requests.get(AGENT + CURRENT + "?path=//DataItem[@id=%27sensor1%27]")
        ) # current Object

        lastSeq = Current.lastSeq # current last sequence
        print('Last Sequence:', lastSeq)
        print('Timestamp:', Current.timestamp)

        x = get_sound_signal(
            requests.get(
                AGENT + SAMPLE + "?from=" + str(int(lastSeq - N)) + "&count=" + str(N) + "&path=//DataItem[@id=%27sensor1%27]"
            )
        ) # request MTConnect sound streams as many as we need

        print('Sound level:', get_sound_level(x), 'dB')

        X = feature_extraction(x) # Input feature for CNN model
        X_tensor = torch.tensor(X, dtype=torch.float32).to(device)

        with torch.no_grad():
            yhat_logits = model(X_tensor) # raw logits
            yhat_probs = torch.softmax(yhat_logits, dim=1) # convert logits to probabilities for interpretation
            yhat = yhat_probs.cpu().numpy()

        print('Model output:', yhat) # the output (yhat) is an array of probabilities of the three classes ([0]:OFF/[1]:ON-airleaking/[2]:ON-vacuum)

        Y = int(np.argmax(yhat, axis=1)[0]) # it returns maximum value (highest probability) from the target function
        print('Prediction inference index:', Y)

        if Y == 0: # if Y is 0, do below
            prediction_label = "OFF"
        elif Y == 1:
            prediction_label = "ON/airleaking"
        elif Y == 2:
            prediction_label = "ON/vacuum"
        else:
            prediction_label = "Unknown"

        print('The pump is now {}.\n'.format(prediction_label))

        time.sleep(1) # pause for 1 second