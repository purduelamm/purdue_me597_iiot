#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import board
import adafruit_dht
import psutil
import time

# Kill libgpio process, if already used.
for p in psutil.process_iter():
    if p.name() == 'libgpiod_pulsei' or p.name() == 'libgpiod_pulsein':
        p.kill()

sensor = adafruit_dht.DHT11(board.D23) #sensor object for DHT11 sensor, D23 means Pin23 of Raspberry Pi

# Continuous printing out Temperature and Humidity every 3 seconds
while True:
    try:
        # To halt this loop, short-cut is CTRL+C
        temperature = sensor.temperature # temperature instance
        humidity = sensor.humidity # humidity instance
        
        # if error occurs, go to except
        
        print("Temperature:{}°C, Humidity:{}%RH".format(temperature, humidity))
        time.sleep(3)
    
    except RuntimeError as e:
        # DHT11 make errors often becuase of reading data.
        # print error and continue.
        print(e.args[0])
        time.sleep(3)
        pass
    
    except Exception as e:
        # If DHT is not detected, break and stop this script.
        dhtDevice.exit()
        raise e
