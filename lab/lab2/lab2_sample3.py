#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ME597-IIoT Implmt. for Smrt Mfg.
Lab2 - sample code 3: increase data rate
"""

import time
import board
import busio
import adafruit_adxl34x
from micropython import const
import csv

# i2c variable defines I2C interfaces and GPIO pins using busio and board modules
i2c = busio.I2C(board.SCL, board.SDA)

# acc object is instantiation using i2c of Adafruit ADXL34X library 
acc = adafruit_adxl34x.ADXL345(i2c)

# acc.data_rate, 0b means binary. 1010 = 10 = 100 Hz Output data rate
# so, if you want to change the output data rate as 3200 Hz, set it to 1111
# to change back to default (0.1 Hz), set it to 0000
acc.data_rate = const(0b1010)

# ratedict=output rate dictionary
# See Table5 of Lab3 manual key=rate code (decimal), value=output data rate (Hz)
ratedict = {15:3200,14:1600,13:800,12:400,11:200,10:100,9:50,8:25,7:12.5,6:6.25,5:3.13,4:1.56,3:0.78,2:0.39,1:0.2,0:0.1}

print("Output data rate is {} Hz.".format(ratedict[acc.data_rate]))
