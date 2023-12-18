import time
import board
import busio
import adafruit_adxl34x
from micropython import const
import csv
import datetime
import numpy as np
from scipy import stats

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

while True:
    try:
        x,y,z = measureData(acc, 1000)
        x_time = timeFeatures(x) # x-axis time feature
        y_time = timeFeatures(y) # y-axis time feature
        z_time = timeFeatures(z) # z-axis time features
        print("X-axis rms={0:.4f} m/s2, Y-axis rms={1:.4f} m/s2, Z-axis rms={2:.4f} m/s2".format(x_time[2], y_time[2], z_time[2]))
    except KeyboardInterrupt:
        # To halt program, press Ctrl + c
        raise
