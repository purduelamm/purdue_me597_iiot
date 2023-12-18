from xml.etree import ElementTree as ET
import requests
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import math
import tensorflow as tf
import time
import datetime
from data_item import Event, Sample
from mtconnect_adapter import Adapter
import sys

## == GLOBAL CONSTANT ==
SAMPLE = "sample" # sample string for MTConnect HTML sample method
CURRENT = "current" # current string for MTConnect HTML current method
SAMP_RATE = int(??) # sampling rate
*SAMP_RATE* = int(?) # sampling rate
*CHUNK* = int(?) # chunk size
*AGENT* = "http://?ip?:?port?/" # MTConnect agent ip:port

*N* = int(?) # number of sequence to take sound
*N_FFT* = int(?) # number of FFT
*N_MELS* = int(?) # number of Mel filter bank

model_file = '20230309_212154_Prelab10_CNN_model1.h5' # CNN model fileanme. Note that this file must be in the same directory

model_keras = tf.keras.models.load_model(model_file, compile=False) # keras model, no need to compile
model_converter = tf.lite.TFLiteConverter.from_keras_model(model_keras) # tensorflow lite model

interpreter = tf.lite.Interpreter(model_content=model_converter.convert()) # interpreter object by tensorflor lite model


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



class MTConnectAdapter(object):

    def __init__(self, host, port):
        # MTConnect adapter connection info
        self.host = host
        self.port = port
        self.adapter = Adapter((host, port))

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

        # MTConnnect adapter availability
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
                Current = CurrentParsing(requests.get(AGENT+CURRENT+"?path=//DataItem[@id=%27sensor1%27]")) # current Object
                lastSeq = Current.lastSeq # current last sequence
                x = get_sound_signal(requests.get(AGENT+SAMPLE+"?from="+str(int(lastSeq-N))+"&count="+str(N)+"&path=//DataItem[@id=%27sensor1%27]")) # request MTConnect sound streams as many as we need
                X = feature_extraction(x) # input feature for CNN model

                interpreter.allocate_tensors() # allocate (initialize) tensors to interpreter
                output = interpreter.get_output_details()[0] # get output from interpreter
                input = interpreter.get_input_details()[0] # get input from interpreter

                interpreter.set_tensor(input['index'], X) # feed the input feature to the CNN model
                interpreter.invoke() # invoke CNN model prediction

                yhat = interpreter.get_tensor(output['index']) # model output as yhat
                Y = yhat.argmax() # it returns maximum value (highest probability) from target function (among elements)

                ## Your algorithm here
                if Y == 0: # label[0]: OFF --> execution:OFF, vacuum_state:N/A
                    exe = "OFF"
                    vs = "N/A"
                elif Y == 1: # label[1]: ON-airleaking --> execution:ON, vacuum_state:N/A
                    exe = "ON"
                    vs = "Air leaking"
                else: # label[2]: ON-vacuuming --> execution:ON, vacuum_state: N/A
                    exe = "ON"
                    vs = "Vacuuming"

                sound_pressure = round(get_sound_level(x),2) # SPL round up 2 to decimal points

                # start taking MTConnect data entities
                self.adapter.begin_gather()
                self.execution.set_value(exe)
                self.vacuum_state.set_value(vs)
                self.sound_level.set_value(sound_pressure)
                self.adapter.complete_gather()
                # end taking MTconnect data entities


                print("{}, Pump is now {} and {} state in {} dB SPL.".format(Current.timestamp,exe,vs,sound_pressure))

                time.sleep(2) # wait for 2 seconds (comment out this if you want to run without wait)

            except KeyboardInterrupt:
                print("Stopping MTConnect...")
                self.adapter.stop() # Stop adapter thread
                sys.exit()


## =================== MAIN =====================

if __name__=="__main__":
    print("Starting Up!")
    MTConnectAdapter('127.0.0.1', 7878) # Args: host ip, port number
