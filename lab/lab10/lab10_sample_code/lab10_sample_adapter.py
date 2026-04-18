from xml.etree import ElementTree as ET
import requests
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import time
import datetime
from data_item import Event, Sample
from mtconnect_adapter import Adapter
import sys

## == GLOBAL CONSTANT ==
SAMPLE = "sample" # sample string for MTConnect HTML sample method
CURRENT = "current" # current string for MTConnect HTML current method
*SAMP_RATE* = int(?) # sampling rate
*CHUNK* = int(?) # chunk size
*AGENT* = "http://?ip?:?port?/" # MTConnect agent ip:port

*N* = int(?) # number of sequence to take sound
*N_FFT* = int(?) # number of FFT
*N_MELS* = int(?) # number of Mel filter bank

*MODEL_FILE* = '**your_model_name.pth**' # PyTorch checkpoint file name. Note that this file must be in the same directory


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
        x = x.unsqueeze(1) # reshape to (batch, 1, height, width)
        x = F.relu(self.conv1(x))
        x = self.pool1(x)
        x = F.relu(self.conv2(x))
        x = self.pool2(x)
        x = torch.flatten(x, start_dim=1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x) # raw logits, no softmax here
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
    S = np.reshape(X, (1, -1, X.shape[1])) # reshaping (1, n, m) : The first dimension is batch size
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


class MTConnectAdapter(object):

    def __init__(self, host, port, model, classes, device):
        # MTConnect adapter connection info
        self.host = host
        self.port = port
        self.adapter = Adapter((host, port))
        self.model = model
        self.classes = classes
        self.device = device

        # For samples
        self.sound_level = Sample('spl') # self.sound_level takes 'spl' data item id.
        self.adapter.add_data_item(self.sound_level) # adding self.sound_level as a data item
        ## Add more samples below

        # For events
        self.execution = Event('e1') # self.event takes 'e1' data item name.
        self.adapter.add_data_item(self.execution) # adding self.execution as a data item
        self.vacuum_state = Event('vs1') # self.vacuum_state takes 'vs1' data item name.
        self.adapter.add_data_item(self.vacuum_state) # adding self.vacuum_state as a data item

        ## Add more events below

        # MTConnect adapter availability
        self.avail = Event('avail')
        self.adapter.add_data_item(self.avail)

        # Start MTConnect
        self.adapter.start()
        self.adapter.begin_gather()
        self.avail.set_value("AVAILABLE")
        self.adapter.complete_gather()
        self.adapter_stream()

    def adapter_stream(self):
        while True:
            try:
                Current = CurrentParsing(
                    requests.get(AGENT + CURRENT + "?path=//DataItem[@id=%27sensor1%27]")
                ) # current Object

                lastSeq = Current.lastSeq # current last sequence

                x = get_sound_signal(
                    requests.get(
                        AGENT + SAMPLE + "?from=" + str(int(lastSeq - N)) + "&count=" + str(N) + "&path=//DataItem[@id=%27sensor1%27]"
                    )
                ) # request MTConnect sound streams as many as we need

                X = feature_extraction(x) # input feature for CNN model
                X_tensor = torch.tensor(X, dtype=torch.float32).to(self.device)

                with torch.no_grad():
                    yhat_logits = self.model(X_tensor) # raw logits
                    yhat_probs = torch.softmax(yhat_logits, dim=1) # probability for interpretation
                    yhat = yhat_probs.cpu().numpy()

                Y = yhat.argmax() # it returns maximum value (highest probability) from target function (among elements)

                ## Your algorithm here
                if Y == 0: # label[0]: OFF --> execution:OFF, vacuum_state:N/A
                    exe = "OFF"
                    vs = "N/A"
                elif Y == 1: # label[1]: ON-airleaking --> execution:ON, vacuum_state:N/A
                    exe = "ON"
                    vs = "Air leaking"
                else: # label[2]: ON-vacuuming --> execution:ON, vacuum_state:N/A
                    exe = "ON"
                    vs = "Vacuuming"

                sound_pressure = round(get_sound_level(x), 2) # SPL round up 2 to decimal points

                # start taking MTConnect data entities
                self.adapter.begin_gather()
                self.execution.set_value(exe)
                self.vacuum_state.set_value(vs)
                self.sound_level.set_value(sound_pressure)
                self.adapter.complete_gather()
                # end taking MTConnect data entities

                print("{}, Pump is now {} and {} state in {} dB SPL.".format(Current.timestamp, exe, vs, sound_pressure))

                time.sleep(?) # wait for ? seconds (comment out this if you want to run without wait)

            except KeyboardInterrupt:
                print("Stopping MTConnect...")
                self.adapter.stop() # Stop adapter thread
                sys.exit()


## =================== MAIN =====================

if __name__ == "__main__":
    print("Starting Up!")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, classes, checkpoint = load_model(MODEL_FILE, device)

    print("Model loaded successfully.")
    print("Classes:", classes)

    MTConnectAdapter('?host?', ?port?, model, classes, device) # Args: host ip, port number