from xml.etree import ElementTree as ET
import requests
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import math
import tensorflow as tf
import time

## == GLOBAL CONSTANT ==
SAMPLE = "sample" # sample string for MTConnect HTML sample method
CURRENT = "current" # current string for MTConnect HTML current method
SAMP_RATE = int(48000) # sampling rate
CHUNK = int(2 ** 11) # chunk size
AGENT = "http://192.168.1.4:5001/" # MTConnect agent ip:port

N = 23 # number of sequence to take sound
N_FFT = 2048 # number of FFT
N_MELS = 128 # number of Mel filter bank


# custom function and class to make the code concise

def get_sound_signal(response): # taking sound signal of a series of the MTConnect sequences
    root = ET.fromstring(response.content)
    MTCONNECT_STR = root.tag.split("}")[0]+"}"
    array = []
    for sample in root.iter(MTCONNECT_STR+"DisplacementTimeSeries"):
        chunk = np.fromstring(sample.text, dtype=np.int16, sep=' ') / (2 ** 15)
        array = np.append(array, chunk)
    array = np.array(array, dtype=np.float32)
    return array # sound signal as float array 


def get_sound_level(signal):
    signal_rms = np.sqrt(np.mean(signal ** 2))
    sound_level = 20*math.log10(signal_rms/9.9963e-7)-28.87
    return sound_level


def feature_extraction(x): # feature extraction for CNN model. This must be the same as you trained the model
    M = librosa.feature.melspectrogram(y=x, sr=SAMP_RATE, n_fft=N_FFT, hop_length=int(N_FFT/4), win_length=N_FFT, window='hann', n_mels=N_MELS) # Mel-spectrogram
    X = 2*abs(M)/N_FFT # Taking magnitude for the input feature of the CNN model
    S = np.reshape(X, (1, -1, X.shape[1])) # resahping (1, n, m) : The first dimension is batch size
    return S # input feature of the CNN model as 3D tensor


class CurrentParsing(object): # MTConnect current Object to get last sequence and timestamp
    def __init__(self, response):
        root = ET.fromstring(response.content)
        MTCONNECT_STR = root.tag.split("}")[0]+"}"
        header = root.find("./"+MTCONNECT_STR+"Header")
        header_attribs = header.attrib
        self.nextSeq = int(header_attribs["nextSequence"])
        self.firstSeq = int(header_attribs["firstSequence"])
        self.lastSeq = int(header_attribs["lastSequence"])
        for sample in root.iter(MTCONNECT_STR+"DisplacementTimeSeries"):
            self.timestamp = sample.get('timestamp')


if __name__=="__main__":
    model_file = '20230309_212154_Prelab10_CNN_model1.h5' # CNN model fileanme. Note that this file must be in the same directory

    model_keras = tf.keras.models.load_model(model_file, compile=False) # keras model, no need to compile
    model_converter = tf.lite.TFLiteConverter.from_keras_model(model_keras) # tensorflow lite model

    interpreter = tf.lite.Interpreter(model_content=model_converter.convert()) # interpreter object by tensorflor lite model

    while True:
        Current = CurrentParsing(requests.get(AGENT+CURRENT+"?path=//DataItem[@id=%27sensor1%27]")) # current Object
        lastSeq = Current.lastSeq # current last sequence
        print('Last Sequence:', lastSeq)
        print('Timestamp:', Current.timestamp)
        x = get_sound_signal(requests.get(AGENT+SAMPLE+"?from="+str(int(lastSeq-N))+"&count="+str(N)+"&path=//DataItem[@id=%27sensor1%27]")) # request MTConnect sound streams as many as we need
        print('Sound level:', get_sound_level(x),'dB')
        X = feature_extraction(x) # Input feature for CNN model

        interpreter.allocate_tensors() # allocate (initialize) tensors to interpreter
        output = interpreter.get_output_details()[0] # get output from interpreter
        input = interpreter.get_input_details()[0] # get input from interpreter

        interpreter.set_tensor(input['index'], X) # feed the input feature to the CNN model
        interpreter.invoke() # invoke CNN model prediction

        yhat = interpreter.get_tensor(output['index']) # model output as yhat
        print('Model output:', yhat) # the output (yhat) is an array of probabilities of the three classes ([0]:OFF/[1]:ON-airleaking/[2]:ON-vacuum)
        Y = yhat.argmax() # it returns maximum value (highest probability) from the target function
        print('Prediction inference index:', Y)

        if Y == 0: # if Y is 0, do below
            prediction_label = "OFF"
        # complete your algorithm to take appropriate prediction_label string according to the CNN model result

        print('The pump is now {}.\n'.format(prediction_label))

        time.sleep(1) # pause for 1 second
