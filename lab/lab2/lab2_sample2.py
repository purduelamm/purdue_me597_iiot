#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ME597-IIoT Implmt. for Smrt Mfg.
Lab2 - sample code 2 : Save accelerations in a CSV file
"""

import time
import board
import busio
import adafruit_adxl34x
import datetime
import csv

# i2c variable defines I2C interfaces and GPIO pins using busio and board modules
i2c = busio.I2C(board.SCL, board.SDA)

# acc object is instantiation using i2c of Adafruit ADXL34X library 
acc = adafruit_adxl34x.ADXL345(i2c)

# filename and header
filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_lab2_fan_off.csv"
header = ["Timestamp", "a_x [m/s2]", "a_y [m/s2]", "a_z [m/s2]"]

start = time.time()# start time, unit = second

duration = 120 # data collection duration, unit = second, in this example, duration is 120 seconds, 2 minutes

i = 0 # measurement indicator

# writing to CSV file using csv package
with open(filename, 'w') as f:
    # creating a CSV wiriting object
    write = csv.writer(f)
    
    # writing header on the first row
    write.writerow(header)
    
    while time.time() - start < duration:
        i += 1 # indicator + 1 in every loop
        # timestamp for measurement
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        x_acc, y_acc, z_acc = acc.acceleration
        
        data = [timestamp, str(x_acc), str(y_acc), str(z_acc)] # data list, all elements are string data type
        
        write.writerow(data) # writing measured data
        
        # printing indicator, timestamp, x-axis, y-axis, z-axis accelerations
        print("{}th measurement, {}:\n x-axis={:.4f}m/s^2, y-axis={:.4f}m/s^2, z-axis={:.4f}m/s^2\n".format(i, timestamp, x_acc, y_acc, z_acc))
        
        time.sleep(1)

# gently close the CSV file object
f.close()