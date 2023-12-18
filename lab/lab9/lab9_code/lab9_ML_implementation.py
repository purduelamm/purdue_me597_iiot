import time
import board
import busio
import adafruit_adxl34x
from micropython import const
import csv
import datetime
import numpy as np
from scipy import stats, fft
import tensorflow as tf

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

## ============== MAIN ==============

if __name__ == "__main__":
    model_path = "models/YourModelDirectory/" # model file directory, you must change this!
    model = tf.keras.models.load_model(model_path) # load the model from the path above
    threshold = # threshold (MAE loss) for the ML model
    min_val = # minimum value for normalization
    max_val = # maximum value for normalization

    while True:
        try:
            x, y, z = measureData(acc, 1000) # x=x-axis, y=y-axis, z-axis acceleration array
            input_feature = # your input feature
            input_feature_normalized = tensorNormalization(input_feature, min_val, max_val) # normalized input feature
            result = predict(model, FINAL_FEATURE_INPUT, threshold) # your model result: bool: True or False
            now = datetime.datetime.now() # datetime now
            print("{0}:Model result={1}, MAE loss={2:.4f}.".format(now, result[0], result[1]))
        except KeyboardInterrupt:
            # to halt, press Ctrl + c
            raise