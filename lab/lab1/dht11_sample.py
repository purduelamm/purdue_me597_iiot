#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import board
import adafruit_dht
import psutil

# Kill libgpio process, if already used.
for p in psutil.process_iter():
    if p.name() == 'libgpiod_pulsei' or p.name() == 'libgpiod_pulsein':
        p.kill()

sensor = adafruit_dht.DHT11(board.D23) #sensor object for DHT11 sensor, D23 means Pin23 of Raspberry Pi

temperature = sensor.temperature # temperature instance
humidity = sensor.humidity # humidity instance

print("Temperature:{}°C, Humidity:{}%RH".format(temperature, humidity))
