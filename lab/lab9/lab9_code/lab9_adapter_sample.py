# MTConnet adapter sample for ME597 Lab10
# Copyright 
# Example for Sample and Event

import sys
import time
import datetime
import board
import busio
import adafruit_adxl34x
from micropython import const
import numpy as np
from scipy import stats, fft
import tensorflow as tf
from data_item import Event, Sample # load data_item package
from mtconnect_adapter import Adapter # load mtconnect_adapter package


i2c = busio.I2C(board.SCL, board.SDA) # i2c variable defines I2C interfaces and GPIO pins using busio and board modules
acc = adafruit_adxl34x.ADXL345(i2c) # acc object is instantiation using i2c of Adafruit ADXL34X library
acc.data_rate = const(0b1111) # change sampling rate as 3200 Hz

# ratedict=output rate dictionary
# See Table5 of Lab3 manual key=rate code (decimal), value=output data rate (Hz)
ratedict = {15:3200,14:1600,13:800,12:400,11:200,10:100,9:50,8:25,7:12.5,6:6.25,5:3.13,4:1.56,3:0.78,2:0.39,1:0.2,0:0.1}
print("Output data rate is {} Hz".format(ratedict[acc.data_rate])) # printing out data rate

def measureData(sensor:object, N:int): # measuring raw data
    data_x, data_y, data_z = [], [], []
    for i in range(N):
        x_acc, y_acc, z_acc = sensor.acceleration
        data_x.append(x_acc)
        data_y.append(y_acc)
        data_z.append(z_acc)
    x_data, y_data, z_data = np.array(data_x), np.array(data_y), np.array(data_z)
    return x_data, y_data, z_data

def timeFeatures(data): # time domain signal processing
    mean = np.mean(data) # mean
    std = np.std(data) # standard deviation
    rms = np.sqrt(np.mean(data ** 2)) # root mean square
    peak = np.max(abs(data)) # peak
    skew = stats.skew(data) # skewness
    kurt = stats.kurtosis(data) # kurtosis
    cf = peak/rms # crest factor
    feature = np.array([mean, std, rms, peak, skew, kurt, cf], dtype=float) # number of features is 7
    return feature # numpy array, each element data type = float

def freqFeatures(data): # freq domain signal processing
    N = len(data) # length of the data (must be 1000)
    yf = 2/N*np.abs(fft.fft(data)[:N//2]) # yf is DFT signal magnitude
    yf[0] = 0
    feature = np.array(yf, dtype=float) # feature array  
    return feature # numpy array, each element data type = float

def tensorNormalization(data, min_val, max_val): # data input as numpy array, min, max
    data_normal = (data - min_val) / (max_val - min_val) 
    tensor = tf.cast(data_normal, tf.float32)
    tensor_feature = tf.reshape(tensor, [-1, len(tensor)])
    return tensor_feature

def predict(model, data, threshold):
    reconstruction = model(data)
    loss = tf.keras.losses.mae(reconstruction, data).numpy()
    result = tf.math.less(loss, threshold).numpy()
    return result[0], loss[0]


class MTConnectAdapter(object): # MTConnect adapter object

    def __init__(self, host, port): # init of MTconnectAdapter class
        # MTConnect adapter connection info
        self.host = host # host arg of adapter
        self.port = port # port arg of adapter
        self.adapter = Adapter((host, port))

        # For samples
        self.Xacc = Sample('Xacc')
        self.adapter.add_data_item(self.Xacc)
        self.Yacc = Sample('Yacc')
        self.adapter.add_data_item(self.Yacc)
        self.Zacc = Sample('Zacc')
        self.adapter.add_data_item(self.Zacc)
        self.mae = Sample('mae')
        self.adapter.add_data_item(self.mae)        
        ## Add more samples below, if needed.

        # For events
        self.execution = Event('execution')
        self.adapter.add_data_item(self.execution)
        self.condition = Event('condition')
        self.adapter.add_data_item(self.condition)
        ## Add more events below, if needed.

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
                x, y, z = measureData(acc,1000) # x=x-axis, y=y-axis, z-axis acceleration array
                input_feature = # your input feature
                input_feature_normalized = tensorNormalization(input_feature, ???, ???) # normalized input feature
                result = predict(model, FINAL_FEATURE_INPUT, threshold)
                x_rms = timeFeatures(x)[2] # calculate rms of x-axis
                y_rms =  # calculate rms of y-axis
                z_rms =  # calculate rms of z-axis
                mae = result[?] # mean absolute error (loss) of the model
                
                if AFF is running:
                    execution = 'ACTIVE'
                    if AFF is normal:
                        condition = 'NORMAL'
                    else:
                        condition = 'ABNORMAL'
                else:
                    execution = 'STOPPED'
                    condition = 'UNAVAILABLE'

                now = datetime.datetime.now() # get current data time
                
                self.adapter.begin_gather() # start to collection
                
                self.Xacc.set_value(str(???))
                self.Yacc.set_value(str(???))
                self.Zacc.set_value(str(???))
                self.execution.set_value(str(???))
                self.condition.set_value(str(???))
                self.mae.set_value(str(???))
                
                self.adapter.complete_gather() # end of collection

                print("{} MTConnect data collection completed ... ".format(now)) # Printing out completed MTConnect collectiones
                print("X-axis rms={0:.4f} m/s2, Y-axis rms={1:.4f} m/s2, Z-axis rms={2:.4f} m/s2".format(x_rms,y_rms,z_rms))
                print("Execution={0}, condition={1}, loss={2:.4f}.\n".format(execution,condition,mae))

                # print("Power meter: Machine is now {}, {} W\n".format(ps,p1)) # Printing out Power meter measured values

            except KeyboardInterrupt: # To stop MTConnect adapter, Ctrl + c
                print("Stopping MTConnect...")
                self.adapter.stop() # Stop adapter thread
                sys.exit() # Terminate Python


## ====================== MAIN ======================
if __name__ == "__main__":
    model_path = "model/YourModelDirectory/" # model file directory, you must change this!
    model = tf.keras.models.load_model(model_path) # load the model from the path above
    threshold =  # float: threshold (MAE loss) for the ML model
    min_val =  # float: minimum value for normalization
    max_val =  # float: maximum value for normalization
    
    # start MTConnect Adapter
    MTConnectAdapter(???, ???) # Args: host ip, port number

